"""Analisi statistica del dataset WiFi con i metodi della performance analysis:
statistica descrittiva, intervalli di confidenza, test di ipotesi, Mann-Kendall, DoE e ANOVA."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np
import pandas as pd
from scipy import stats

from core.linkability import _ordered_pairs
from core.privacy_optimizer import COUNTER_LEVELS, PLACE_LEVELS, TIME_LEVELS, Variant, publish


def describe(series: pd.Series) -> dict[str, float]:
    """Indici di tendenza centrale e dispersione; con forte asimmetria la mediana è l'indice corretto."""
    values = series.dropna().astype(float)
    q1, q3 = np.percentile(values, [25, 75])
    return {
        "media": values.mean(), "mediana": values.median(), "dev. standard": values.std(ddof=1),
        "COV": values.std(ddof=1) / values.mean() if values.mean() else np.nan,
        "SIQR": (q3 - q1) / 2, "asimmetria": float(stats.skew(values)), "n": len(values),
    }


def mean_ci(values: np.ndarray, confidence: float = 0.95) -> tuple[float, float, float]:
    """Media e intervallo di confidenza con t di Student (n < 30) su n-1 gradi di libertà."""
    values = np.asarray(values, dtype=float)
    mean, sem = values.mean(), stats.sem(values)
    half = stats.t.ppf((1 + confidence) / 2, len(values) - 1) * sem
    return mean, mean - half, mean + half


def mann_kendall(values: np.ndarray) -> tuple[float, float]:
    """Tau di Kendall rispetto al tempo e p-value bilaterale, con correzione per i pareggi."""
    x = np.asarray(values, dtype=float)
    n = len(x)
    if n < 4:
        return np.nan, np.nan
    s = sum(np.sign(x[j] - x[i]) for i in range(n - 1) for j in range(i + 1, n))
    _, counts = np.unique(x, return_counts=True)
    variance = (n * (n - 1) * (2 * n + 5) - sum(t * (t - 1) * (2 * t + 5) for t in counts)) / 18
    z = 0.0 if s == 0 else (s - np.sign(s)) / np.sqrt(variance)
    return s / (n * (n - 1) / 2), 2 * stats.norm.sf(abs(z))


@dataclass(frozen=True)
class FlawEvidence:
    binomial_p: float
    ordered_share: float
    pairs: int
    sites_tested: int
    sites_increasing: int
    daily_unique: pd.Series
    daily_ci: tuple[float, float, float]


@dataclass(frozen=True)
class DailyOrderEvidence:
    days: pd.DataFrame
    observed_mean: float
    null_mean: float
    wilcoxon_p: float
    effect_ci: tuple[float, float]


@dataclass(frozen=True)
class CrossDayEvidence:
    day_pairs: int
    comparisons: int
    observed_share: float
    null_mean: float
    null_ci: tuple[float, float]
    empirical_p: float


def daily_order_evidence(
    frame: pd.DataFrame, max_step: int = 3, min_pairs: int = 50, seed: int = 42
) -> DailyOrderEvidence:
    """Replica il test dell'ordine separatamente per giorno.

    Il confronto appaiato tra dato reale e permutato usa il giorno come unità
    indipendente, evitando di trattare come indipendenti migliaia di coppie
    provenienti dalla stessa giornata.
    """
    rng = np.random.default_rng(seed)
    rows = []
    work = frame.assign(_day=frame["inizio"].dt.date, _ts=frame["inizio"])
    for day, daily in work.groupby("_day"):
        pairs = ordered = null_ordered = 0
        for _, group in daily.groupby(["sede", "DTLN"], sort=False):
            if len(group) < 2:
                continue
            values = group.sort_values("_ts")["LOGINCOUNT"].to_numpy(dtype=float)
            current_pairs, current_ordered = _ordered_pairs(values, max_step)
            _, current_null = _ordered_pairs(rng.permutation(values), max_step)
            pairs += current_pairs
            ordered += current_ordered
            null_ordered += current_null
        if pairs >= min_pairs:
            rows.append({
                "giorno": str(day), "coppie": pairs,
                "osservato": ordered / pairs, "permutato": null_ordered / pairs,
            })
    days = pd.DataFrame(rows)
    if days.empty:
        raise ValueError("Non ci sono abbastanza coppie giornaliere per il test.")
    differences = (days["osservato"] - days["permutato"]).to_numpy()
    wilcoxon_p = float(stats.wilcoxon(days["osservato"], days["permutato"], alternative="greater").pvalue)
    # Bootstrap sui giorni, non sulle coppie: conserva l'unità di replica corretta.
    boot = np.array([
        rng.choice(differences, size=len(differences), replace=True).mean() for _ in range(5000)
    ])
    return DailyOrderEvidence(
        days=days,
        observed_mean=float(days["osservato"].mean()),
        null_mean=float(days["permutato"].mean()),
        wilcoxon_p=wilcoxon_p,
        effect_ci=(float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))),
    )


def cross_day_evidence(
    frame: pd.DataFrame, max_growth: int = 5, permutations: int = 500, seed: int = 42
) -> CrossDayEvidence:
    """Cerca continuità di LOGINCOUNT tra giorni consecutivi.

    Una corrispondenza richiede stessa sede e lingua e un valore nel giorno
    successivo compreso tra v e v+max_growth. La permutazione conserva valori,
    giorni e numerosità ma spezza l'associazione con sede e lingua.
    """
    work = frame.copy()
    work["_day"] = pd.to_datetime(work["giorno"])
    groups = pd.Series(list(zip(work["sede"].astype(str), work["DTLN"].astype(str))), index=work.index)
    work["_group"] = pd.factorize(groups)[0].astype(np.int64)
    work["_value"] = work["LOGINCOUNT"].astype(np.int64)
    base = int(work["_value"].max() + max_growth + 2)
    available = set(work["_day"].unique())
    day_pairs: list[tuple[np.ndarray, np.ndarray]] = []
    for day in sorted(available):
        next_day = day + np.timedelta64(1, "D")
        if next_day not in available:
            continue
        current = work.loc[work["_day"] == day, ["_group", "_value"]].drop_duplicates().to_numpy(np.int64)
        following = work.loc[work["_day"] == next_day, ["_group", "_value"]].drop_duplicates().to_numpy(np.int64)
        day_pairs.append((current, following))
    if not day_pairs:
        raise ValueError("Servono almeno due giornate consecutive.")

    def match_rate(shuffle: bool, rng: np.random.Generator) -> tuple[float, int]:
        hits = comparisons = 0
        for current, following in day_pairs:
            values = rng.permutation(following[:, 1]) if shuffle else following[:, 1]
            next_codes = np.unique(following[:, 0] * base + values)
            current_codes = current[:, 0] * base + current[:, 1]
            matched = np.zeros(len(current_codes), dtype=bool)
            for delta in range(max_growth + 1):
                matched |= np.isin(current_codes + delta, next_codes)
            hits += int(matched.sum())
            comparisons += len(matched)
        return hits / comparisons, comparisons

    rng = np.random.default_rng(seed)
    observed, comparisons = match_rate(False, rng)
    null = np.array([match_rate(True, rng)[0] for _ in range(permutations)])
    return CrossDayEvidence(
        day_pairs=len(day_pairs), comparisons=comparisons, observed_share=observed,
        null_mean=float(null.mean()),
        null_ci=(float(np.quantile(null, 0.025)), float(np.quantile(null, 0.975))),
        empirical_p=float((1 + (null >= observed).sum()) / (permutations + 1)),
    )


def flaw_evidence(frame: pd.DataFrame, ordered_share: float, pairs: int) -> FlawEvidence:
    """H0: tra valori vicini non esiste ordinamento temporale (probabilità 0,5).
    Mann-Kendall per sede: se LOGINCOUNT fosse un contatore di sede, crescerebbe nel tempo in ogni sede."""
    ordered = round(ordered_share * pairs)
    binomial_p = stats.binomtest(ordered, pairs, 0.5, alternative="greater").pvalue
    increasing, tested = 0, 0
    for _, site in frame.sort_values("inizio").groupby("sede"):
        if len(site) < 30:
            continue
        tau, p = mann_kendall(site["LOGINCOUNT"].to_numpy()[:400])
        tested += 1
        increasing += int(p < 0.05 and tau > 0.5)
    keys = ["giorno", "STARTTIME", "sede", "DTLN"]
    unique = frame.groupby(keys)["giorno"].transform("size").eq(1)
    daily = unique.groupby(frame["giorno"]).mean()
    daily = daily[frame.groupby("giorno").size().reindex(daily.index) >= 200]
    return FlawEvidence(binomial_p, ordered_share, pairs, tested, increasing, daily, mean_ci(daily.to_numpy()))


def factorial_responses(frame: pd.DataFrame) -> pd.DataFrame:
    """Full factorial 4×3×3: per ogni versione e ogni giorno (replica) misura la quota di sessioni uniche."""
    days = frame.groupby("giorno").size()
    keep = frame[frame["giorno"].isin(days[days >= 200].index)]
    rows = []
    for time, place, counter in product(TIME_LEVELS, PLACE_LEVELS, COUNTER_LEVELS):
        published = publish(keep, Variant(time, place, counter))
        keys = ["giorno", "orario", "luogo", "lingua"] + (["contatore"] if "contatore" in published else [])
        unique = published.groupby(keys, dropna=False)["giorno"].transform("size").eq(1)
        for day, share in unique.groupby(published["giorno"]).mean().items():
            rows.append({"orario": time, "luogo": place, "contatore": counter, "giorno": day, "rischio": share})
    return pd.DataFrame(rows)


def anova_three_factors(data: pd.DataFrame, response: str = "rischio",
                        factors: tuple[str, str, str] = ("orario", "luogo", "contatore")) -> pd.DataFrame:
    """ANOVA a tre fattori con repliche (disegno bilanciato): SS, importanza SS/SST, F e p-value."""
    a, b, c = factors
    y = data[response]
    grand = y.mean()
    levels = {f: data[f].nunique() for f in factors}
    replicas = len(data) // np.prod(list(levels.values()))
    m = {f: data.groupby(f)[response].mean() for f in factors}
    mab, mac, mbc = (data.groupby([p, q])[response].mean() for p, q in ((a, b), (a, c), (b, c)))
    mabc = data.groupby([a, b, c])[response].mean()
    ss: dict[str, float] = {}
    for f in factors:
        others = np.prod([levels[g] for g in factors if g != f]) * replicas
        ss[f] = others * ((m[f] - grand) ** 2).sum()
    for (p, q), means in (((a, b), mab), ((a, c), mac), ((b, c), mbc)):
        other = [g for g in factors if g not in (p, q)][0]
        effect = means - means.index.get_level_values(0).map(m[p]).to_numpy() - means.index.get_level_values(1).map(m[q]).to_numpy() + grand
        ss[f"{p} × {q}"] = levels[other] * replicas * (effect ** 2).sum()
    idx = mabc.index
    interaction3 = (
        mabc.to_numpy()
        - mab.reindex(list(zip(idx.get_level_values(0), idx.get_level_values(1)))).to_numpy()
        - mac.reindex(list(zip(idx.get_level_values(0), idx.get_level_values(2)))).to_numpy()
        - mbc.reindex(list(zip(idx.get_level_values(1), idx.get_level_values(2)))).to_numpy()
        + idx.get_level_values(0).map(m[a]).to_numpy() + idx.get_level_values(1).map(m[b]).to_numpy()
        + idx.get_level_values(2).map(m[c]).to_numpy() - grand
    )
    ss[f"{a} × {b} × {c}"] = replicas * (interaction3 ** 2).sum()
    cell = data.groupby([a, b, c])[response].transform("mean")
    sse = ((y - cell) ** 2).sum()
    sst = ((y - grand) ** 2).sum()
    la, lb, lc = (levels[f] for f in factors)
    dof = {a: la - 1, b: lb - 1, c: lc - 1, f"{a} × {b}": (la - 1) * (lb - 1), f"{a} × {c}": (la - 1) * (lc - 1),
           f"{b} × {c}": (lb - 1) * (lc - 1), f"{a} × {b} × {c}": (la - 1) * (lb - 1) * (lc - 1)}
    dof_error = la * lb * lc * (replicas - 1)
    mse = sse / dof_error
    rows = [
        {"fonte": name, "SS": value, "importanza": value / sst, "gdl": dof[name],
         "F": (value / dof[name]) / mse, "p-value": stats.f.sf((value / dof[name]) / mse, dof[name], dof_error)}
        for name, value in ss.items()
    ]
    rows.append({"fonte": "errore (tra giorni)", "SS": sse, "importanza": sse / sst, "gdl": dof_error, "F": np.nan, "p-value": np.nan})
    return pd.DataFrame(rows).sort_values("importanza", ascending=False)


def paired_comparison(responses: pd.DataFrame, chosen: dict[str, str]) -> dict[str, float]:
    """Stessi giorni prima e dopo la correzione: IC 95% della differenza e Wilcoxon signed-rank."""
    def series(time: str, place: str, counter: str) -> pd.Series:
        mask = (responses["orario"] == time) & (responses["luogo"] == place) & (responses["contatore"] == counter)
        return responses[mask].set_index("giorno")["rischio"]

    before = series("secondo", "civico", "pubblicato")
    after = series(chosen["orario"], chosen["luogo"], chosen["contatore"]).reindex(before.index)
    difference = (before - after).to_numpy()
    mean, low, high = mean_ci(difference)
    return {
        "giorni": len(difference), "differenza media": mean, "IC basso": low, "IC alto": high,
        "Wilcoxon p-value": stats.wilcoxon(difference).pvalue,
        "Shapiro p-value (normalità)": stats.shapiro(difference).pvalue if len(difference) >= 3 else np.nan,
    }
