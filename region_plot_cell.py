from collections import OrderedDict


# --- stacking order, RUNBOOK PLOT-01 --------------------------------------
# The paper stacks processes in a FIXED physics order (bottom to top), not by
# yield. Sorting by yield puts the largest process at the bottom, which for the
# single-lepton channel (ttbar dominant) inverts the picture completely: the
# same numbers produce a stack that looks nothing like Figure 4.
# Read off the legends of Figures 4 and 5, bottom of the stack first:
PAPER_STACK_ORDER = ["Diboson", "tX", "ttbar", "WJets", "Zvv", "Zll"]


def plot_region_stack(dfs_dict, region_name, var_name, x_label, x_range,
                      channel_label, n_bins=10, y_span=(1000.0, 150.0),
                      overflow=True, lumi_label=None):
    """Stacked MC vs data with a Data/Bkg ratio panel underneath.

    Laid out like Figures 4 and 5 of the paper: log-scale main panel, ratio
    panel below with a line at 1. The upstream version had no ratio panel,
    which is the panel that actually shows whether data and simulation agree.

    RUNBOOK PLOT-01: processes are stacked in the paper's fixed order.
    RUNBOOK PLOT-03: the last bin absorbs the overflow, as the captions of
    Figures 4 and 5 state ("The last bin contains overflow events"). Without
    it our last bin falls off while the paper's rises, which is the single
    most visible shape difference in the comparison.
    """
    bins = np.linspace(x_range[0], x_range[1], n_bins + 1)
    centers = 0.5 * (bins[1:] + bins[:-1])
    hi_edge = bins[-1]

    def _hist(values, weights=None):
        v = np.asarray(values, dtype=float)
        if overflow:
            # Push everything above the last edge into the last bin. Clipping
            # just below the edge keeps np.histogram from dropping it.
            v = np.minimum(v, hi_edge - 1e-9)
        return np.histogram(v, bins=bins, weights=weights)[0]

    grouped_counts, grouped_info = {}, {}
    for name, df in dfs_dict.items():
        if name in DATA_SL:
            continue
        counts = _hist(df[var_name], weights=df["final_weight"])
        g, label, color = get_group_info(name)
        if g not in grouped_counts:
            grouped_counts[g] = counts
            grouped_info[g] = {"label": label, "color": color, "yield": counts.sum()}
        else:
            grouped_counts[g] += counts
            grouped_info[g]["yield"] += counts.sum()

    # PLOT-01: the paper's order, restricted to the groups actually present.
    order = [g for g in PAPER_STACK_ORDER if g in grouped_counts]
    order += [g for g in grouped_counts if g not in PAPER_STACK_ORDER]

    mc_counts = [grouped_counts[g] for g in order]
    mc_colors = [grouped_info[g]["color"] for g in order]
    mc_labels = [grouped_info[g]["label"] for g in order]
    total_mc = np.sum(mc_counts, axis=0) if mc_counts else np.zeros(n_bins)

    df_data = dfs_dict.get(channel_label)
    data_counts = (_hist(df_data[var_name]) if df_data is not None
                   else np.zeros(n_bins))

    fig, (ax, rax) = plt.subplots(
        2, 1, figsize=(9, 9), sharex=True,
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05})

    if mc_counts:
        hep.histplot(mc_counts, bins=bins, stack=True, histtype="fill",
                     color=mc_colors, label=mc_labels,
                     edgecolor="black", linewidth=0.7, ax=ax)
    hep.histplot(data_counts, bins=bins, histtype="errorbar", color="black",
                 label="Data", yerr=True, marker="o", markersize=5, ax=ax)

    hep.cms.label("Preliminary", data=True, lumi=lumi_label, year=2016, ax=ax)
    ax.text(0.04, 0.90, region_name, transform=ax.transAxes,
            fontsize=17, fontweight="bold", va="top")

    # RUNBOOK PLOT-05: legend in the paper's reading order -- Data, then the
    # stack from the TOP down: Z(ll), Z(nunu), W(lnu), ttbar, t+X, VV/VH.
    # Relying on the order matplotlib hands back was giving the reverse
    # (bottom-up), so the legend disagreed with the stack it described. Built
    # explicitly from `order` instead, which cannot drift.
    handles, labels = ax.get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles))
    wanted = ["Data"] + [grouped_info[g]["label"] for g in reversed(order)]
    leg_labels = [l for l in wanted if l in by_label]
    leg_labels += [l for l in by_label if l not in leg_labels]
    ax.legend([by_label[l] for l in leg_labels], leg_labels,
              fontsize=13, ncol=2, loc="upper right")
    ax.set_ylabel("Events", fontsize=20)
    ax.set_yscale("log")
    # RUNBOOK PLOT-04: the axis spans the paper's PROPORTIONS, not its absolute
    # range. Open Data gives us 2.4-4.9 fb^-1 against the paper's 35.9, so our
    # stacks sit roughly an order of magnitude lower; pinning the paper's
    # absolute limits would shove our histogram into the bottom of an empty
    # frame and make the comparison look worse than it is. Instead the limits
    # are fixed multiples of the stack peak, chosen to reproduce the decades
    # visible in Figures 4 and 5 (about 3.5 below the peak, 2 above it for the
    # legend). Every panel in a channel therefore has the same dynamic range.
    peak = max(data_counts.max(), total_mc.max(), 1.0)
    ax.set_ylim(peak / y_span[0], peak * y_span[1])

    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(total_mc > 0, data_counts / total_mc, np.nan)
        rerr = np.where(total_mc > 0, np.sqrt(data_counts) / total_mc, np.nan)
    rax.errorbar(centers, ratio, yerr=rerr, fmt="o", color="black", markersize=5)
    rax.axhline(1.0, color="#888888", linestyle="--", linewidth=1)
    rax.set_ylim(0, 2.4)
    rax.set_ylabel("Data / Bkg", fontsize=14)
    rax.set_xlabel(x_label, fontsize=20)
    rax.set_xlim(x_range)
    rax.grid(axis="y", alpha=0.25)

    n_d, n_m = data_counts.sum(), total_mc.sum()
    if n_m:
        rax.text(0.98, 0.86, f"total Data/Bkg = {n_d / n_m:.2f}",
                 transform=rax.transAxes, ha="right", va="top", fontsize=11,
                 color="#444444")

    plt.tight_layout()
    plt.show()
