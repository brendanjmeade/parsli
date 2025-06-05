"""
Image Player application

Usage:

    # Using module name
    python -m parsli.player.app --data /path/to/parsli/export1/ /path/to/parsli/export2/ ...

    # Using script alias
    parsli-player --data /path/to/parsli/export1/ /path/to/parsli/export2/ ...

"""

import asyncio
from pathlib import Path

from trame.app import TrameApp, asynchronous
from trame.decorators import change
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import vuetify3 as v3
from trame.widgets.trame import MouseTrap

LAYOUTS = [
    {"title": 1, "value": 12},
    {"title": 2, "value": 6},
    {"title": 3, "value": 4},
    {"title": 4, "value": 3},
]


class ParsliPlayer(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")
        self.server.cli.add_argument(
            "--data", nargs="+", help="List all export directory you want to load"
        )
        args, _ = self.server.cli.parse_known_args()

        # Serve datasets over http
        http_serve = {}
        n_timesteps = []
        for idx, data_path in enumerate(args.data, start=1):
            ds_path = Path(data_path).resolve()
            n_timesteps.append(len(list(ds_path.glob("*.png"))))
            http_serve[f"{idx}"] = str(ds_path)
        self.server.enable_module({"serve": http_serve})

        # Extract dataset info
        self.state.trame__title = "Parsli Player"
        self.state.nb_datasets = len(args.data)
        self.state.time_max = n_timesteps[0] - 1
        self.state.time_index = 0
        assert sum(n_timesteps) == n_timesteps[0] * self.state.nb_datasets

        # Build UI
        with VAppLayout(self.server, full_height=True) as self.ui:
            with MouseTrap(
                next="time_index < time_max && time_index++",
                prev="time_index && time_index--",
                start="time_index = 0",
                end="time_index = time_max",
                togglePlay="playing = !playing",
            ) as mt:
                mt.bind(["right"], "next")
                mt.bind(["left"], "prev")
                mt.bind(["space"], "togglePlay")
                mt.bind(["home"], "start")
                mt.bind(["end"], "end")
            with v3.VLayout():
                with v3.VMain():
                    with v3.VContainer(classes="h-100 pa-0 ma-0", fluid=True):
                        with v3.VRow(no_gutters=True):
                            with v3.VCol(
                                cols=("nb_cols",),
                                v_for="ds_idx in nb_datasets",
                                key="ds_idx",
                            ):
                                v3.VImg(
                                    src=(
                                        "`/${ds_idx}/${('000000000000' + time_index).slice(-12)}.png`",
                                    ),
                                )
                with v3.VFooter(app=True):
                    v3.VSelect(
                        v_model=("nb_cols", 6),
                        items=("layouts", LAYOUTS),
                        density="compact",
                        hide_details=True,
                        variant="solo",
                        flat=True,
                        style="max-width: 5rem;",
                    )
                    v3.VSlider(
                        v_model=("time_index", 0),
                        max=("time_max", 1),
                        min=0,
                        step=1,
                        density="compact",
                        hide_details=True,
                        classes="mx-2",
                    )
                    v3.VCheckbox(
                        v_model=("playing", False),
                        true_icon="mdi-stop",
                        false_icon="mdi-play",
                        density="compact",
                        hide_details=True,
                        classes="mx-2",
                    )
                    v3.VLabel(
                        "{{ time_index + 1}}/{{ time_max + 1}}",
                        style="width: 100px;",
                        classes="text-right",
                    )

    @property
    def state(self):
        return self.server.state

    @change("playing")
    def on_play(self, playing, **_):
        if playing:
            asynchronous.create_task(self._playing())

    async def _playing(self):
        while self.state.playing:
            with self.state:
                if self.state.time_index < self.state.time_max:
                    self.state.time_index += 1
                else:
                    self.state.playing = False
            await asyncio.sleep(0.1)


def main():
    app = ParsliPlayer()
    app.server.start()


if __name__ == "__main__":
    main()
