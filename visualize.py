import matplotlib.pyplot as plt
from matplotlib import font_manager
from typing import Self, Optional


class Visualizer:
    def __init__(
        self,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        figsize: tuple = (11, 5),
    ):
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.figsize = figsize
        self.series: list[dict] = []
        self.hlines: list[dict] = []
        self.vlines: list[dict] = []

        self.setup()

    def setup(self):
        CJK = {
            "Microsoft YaHei",
            "SimHei",
            "SimSun",
            "KaiTi",
            "STKaiti",
            "STSong",
            "Noto Sans CJK SC",
            "WenQuanYi Zen Hei",
            "Source Han Sans SC",
        }
        available = {f.name for f in font_manager.fontManager.ttflist}
        chosen = next(iter(CJK & available), None)

        if chosen:
            plt.rcParams["font.sans-serif"] = [chosen, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False

    def add(
        self,
        data: list[float],
        name: str = "",
        color: Optional[str] = None,
        linestyle: str = "-",
        linewidth: float = 1.5,
        marker: Optional[str] = None,
        alpha: float = 1.0,
    ) -> Self:
        self.series.append(
            {
                "data": data,
                "label": name,
                "color": color,
                "linestyle": linestyle,
                "linewidth": linewidth,
                "marker": marker,
                "alpha": alpha,
            }
        )
        return self

    def hline(
        self,
        y: float,
        label: str = "",
        color: str = "gray",
        linestyle: str = "--",
        linewidth: float = 1,
    ) -> Self:
        self.hlines.append(
            {
                "y": y,
                "label": label,
                "color": color,
                "linestyle": linestyle,
                "linewidth": linewidth,
            }
        )
        return self

    def vline(
        self,
        x: float,
        label: str = "",
        color: str = "gray",
        linestyle: str = "--",
        linewidth: float = 1,
    ) -> Self:
        self.vlines.append(
            {
                "x": x,
                "label": label,
                "color": color,
                "linestyle": linestyle,
                "linewidth": linewidth,
            }
        )
        return self

    def clear(self):
        self.series.clear()
        self.hlines.clear()
        self.vlines.clear()

    def show(self, path: Optional[str] = None):
        plt.figure(figsize=self.figsize)

        for series in self.series:
            data = series.pop("data")
            plt.plot(data, **series)
            series["data"] = data

        for line in self.hlines:
            plt.axhline(
                line["y"],
                color=line["color"],
                ls=line["linestyle"],
                lw=line["linewidth"],
                label=line["label"] if line["label"] else None,
            )

        for line in self.vlines:
            plt.axvline(
                line["x"],
                color=line["color"],
                ls=line["linestyle"],
                lw=line["linewidth"],
                label=line["label"] if line["label"] else None,
            )

        if self.title:
            plt.title(self.title)
        if self.xlabel:
            plt.xlabel(self.xlabel)
        if self.ylabel:
            plt.ylabel(self.ylabel)

        if (
            any(s["label"] for s in self.series)
            or any(l.get("label") for l in self.hlines)
            or any(l.get("label") for l in self.vlines)
        ):
            plt.legend()

        plt.tight_layout()

        if path:
            plt.savefig(path, dpi=150, bbox_inches="tight")
            print(f"图表已保存至: {path}")
        else:
            plt.show()

        plt.close()
