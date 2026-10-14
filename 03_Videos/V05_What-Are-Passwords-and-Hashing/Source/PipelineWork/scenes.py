"""Manim scene templates for Concept in Motion (v2: narration-synced).

build.py passes each scene's settings through environment variables:
  SCENE_SPEC     JSON with the visual settings from scenes.json
  SCENE_DURATION seconds of narration
  SCENE_CUES     JSON {event_name: seconds}, computed from the phrases you list in "cues",
                 already shifted earlier so each visual lands just BEFORE the words
Keep important visuals out of the bottom-right corner (your watermark lives there).
"""
import json
import os

from manim import *

BG = "#0E1320"
BLUE = "#2E86DE"      # data / API
ORANGE = "#F39C12"    # user / packet
GREEN = "#27AE60"     # server
MIST = "#EAF0FA"
SOFT = "#8FB6E8"
SKIN = "#F6D5B5"
COLORS = {"orange": ORANGE, "blue": BLUE, "green": GREEN}

config.background_color = BG

# Install Poppins (free, Google Fonts) for the channel look, or set FONT = None to use the system default.
FONT = "Poppins"


def T(string, **kw):
    """Text with the channel font."""
    if FONT:
        kw.setdefault("font", FONT)
    return Text(string, **kw)


def spec():
    return json.loads(os.environ.get("SCENE_SPEC", "{}"))


def total():
    return float(os.environ.get("SCENE_DURATION", "6"))


def cues():
    return json.loads(os.environ.get("SCENE_CUES", "{}")) or {}


def at(scene, t):
    """Wait until the narration clock reaches t seconds."""
    d = t - scene.renderer.time
    if d > 0.05:
        scene.wait(d)


def run_events(scene, actions):
    """actions: {name: function}. Each runs at its cue time; a missing cue is spread evenly."""
    c, names, timed = cues(), list(actions), []
    for i, name in enumerate(names):
        t = c.get(name, total() * (0.08 + 0.75 * i / max(len(names), 1)))
        timed.append((t, i, name))
    for t, _, name in sorted(timed):
        at(scene, t)
        actions[name]()


def hold_until_end(scene):
    scene.wait(max(total() - scene.renderer.time, 0.1))


def fit(group, max_width=12.0):
    if group.width > max_width:
        group.scale_to_fit_width(max_width)
    return group


# --------------------------------------------------------------------------- title
class TitleCard(Scene):
    def construct(self):
        s = spec()
        title = T(s.get("title", ""), font_size=58, color=MIST, weight=BOLD)
        group = VGroup(title)
        if s.get("subtitle"):
            sub = T(s["subtitle"], font_size=30, color=SOFT)
            sub.next_to(title, DOWN, buff=0.45)
            group.add(sub)
        fit(group, 11.5).move_to(ORIGIN)
        self.play(FadeIn(group, shift=UP * 0.3), run_time=0.8)
        self.play(Indicate(title, scale_factor=1.06, color=ORANGE), run_time=1.0)
        hold_until_end(self)


# --------------------------------------------------------------------------- bullets
class Bullets(Scene):
    """Each bullet pops in when the narration reaches its cue phrase."""

    def construct(self):
        s = spec()
        items = s.get("items", [])
        title = T(s.get("title", ""), font_size=44, color=MIST, weight=BOLD).to_edge(UP, buff=0.7)
        self.play(FadeIn(title), run_time=0.6)
        rows = VGroup(*[
            VGroup(Dot(color=ORANGE), T(item, font_size=32, color=MIST)).arrange(RIGHT, buff=0.3)
            for item in items
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        fit(rows, 11.5).next_to(title, DOWN, buff=0.8).to_edge(LEFT, buff=1.2)

        def reveal(row):
            def go():
                self.play(FadeIn(row, shift=RIGHT * 0.3), run_time=0.5)
                self.play(Indicate(row[0], scale_factor=1.8), run_time=0.5)
            return go

        run_events(self, {str(i): reveal(r) for i, r in enumerate(rows)})
        hold_until_end(self)


# --------------------------------------------------------------------------- diagram
def make_node(label, color, position):
    box = RoundedRectangle(corner_radius=0.2, width=2.8, height=1.5, color=color, fill_opacity=0.25)
    text = T(label, font_size=28, color=MIST).move_to(box)
    return VGroup(box, text).move_to(position)


class Flow(Scene):
    """App -> API -> Server diagram.
    mode "request" events:  app, server, api, request, check, forward
    mode "response" events: work, response, json, arrive   (nodes are already on screen)
    """

    def construct(self):
        s = spec()
        mode = s.get("mode", "request")
        spec_nodes = s.get("nodes") or [
            {"label": "Your App", "color": "orange"},
            {"label": "API", "color": "blue"},
            {"label": "Server", "color": "green"},
        ]
        app, api, server = [make_node(n["label"], COLORS[n["color"]], RIGHT * x + UP * 0.6)
                            for n, x in zip(spec_nodes, (-4.6, 0, 4.6))]
        arrows = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.1, color=MIST)
                          for a, b in ((app, api), (api, server))])
        if s.get("title"):
            self.add(T(s["title"], font_size=40, color=MIST, weight=BOLD).to_edge(UP, buff=0.6))

        def pop(node):
            return lambda: (self.play(FadeIn(node, scale=0.6), run_time=0.5),
                            self.play(Indicate(node, scale_factor=1.12), run_time=0.6))

        state = {}

        def request_start():
            self.play(GrowArrow(arrows[0]), GrowArrow(arrows[1]), run_time=0.5)
            label = T(s.get("request", "Request"), font_size=26, color=BLUE).next_to(api, UP, buff=0.9)
            packet = Dot(color=BLUE, radius=0.17).move_to(app.get_right())
            state.update(label=label, packet=packet)
            self.play(FadeIn(label), FadeIn(packet), run_time=0.4)
            self.play(packet.animate.move_to(api.get_left()), run_time=1.0)

        def check():
            note = T(s.get("thinking", "Checking the request..."), font_size=24, color=SOFT)
            note.next_to(api, DOWN, buff=0.5)
            state["note"] = note
            self.play(FadeIn(note, shift=UP * 0.2), Indicate(api, scale_factor=1.1), run_time=0.8)

        def forward():
            self.play(FadeOut(state["note"]), run_time=0.3)
            self.play(state["packet"].animate.move_to(server.get_left()), run_time=1.0)
            self.play(FadeOut(state["label"]), FadeOut(state["packet"]), run_time=0.4)

        def work():
            note = T(s.get("thinking", "Looking up data..."), font_size=24, color=SOFT).next_to(server, DOWN, buff=0.5)
            state["note"] = note
            self.play(FadeIn(note, shift=UP * 0.2), Indicate(server, scale_factor=1.1), run_time=0.8)

        def response_start():
            if "note" in state:
                self.play(FadeOut(state["note"]), run_time=0.3)
            label = T(s.get("response", "Response"), font_size=26, color=GREEN).next_to(api, UP, buff=0.9)
            packet = Dot(color=GREEN, radius=0.17).move_to(server.get_left())
            state.update(label=label, packet=packet)
            self.play(FadeIn(label), FadeIn(packet), run_time=0.4)
            self.play(packet.animate.move_to(api.get_right()), run_time=1.0)

        def show_json():
            lines = s.get("json", ["city: Nairobi", "temperature: 24", "condition: light rain"])
            card_text = T("\n".join(lines), font="Monospace", font_size=24, color=MIST, line_spacing=0.9)
            card = RoundedRectangle(corner_radius=0.15, width=card_text.width + 0.6, height=card_text.height + 0.5,
                                    color=GREEN, fill_color="#161C2C", fill_opacity=1)
            block = VGroup(card, card_text.move_to(card)).next_to(api, DOWN, buff=0.5)
            state["card"] = block
            self.play(FadeIn(block, shift=UP * 0.2), run_time=0.7)

        def arrive():
            self.play(state["packet"].animate.move_to(app.get_right()), run_time=1.0)
            self.play(Indicate(app, scale_factor=1.12), FadeOut(state["packet"]), FadeOut(state["label"]), run_time=0.8)

        if mode == "request":
            run_events(self, {"app": pop(app), "server": pop(server), "api": pop(api),
                              "request": request_start, "check": check, "forward": forward})
        else:
            self.add(app, api, server, arrows)
            run_events(self, {"work": work, "response": response_start, "json": show_json, "arrive": arrive})
        hold_until_end(self)


# --------------------------------------------------------------------------- cartoon restaurant
def person(body_color, chef=False, bow=False):
    head = Circle(radius=0.38, fill_color=SKIN, fill_opacity=1, stroke_width=0)
    body = RoundedRectangle(corner_radius=0.25, width=1.1, height=1.2, fill_color=body_color,
                            fill_opacity=1, stroke_width=0).next_to(head, DOWN, buff=-0.06)
    eyes = VGroup(*[Dot(radius=0.05, color=BG).move_to(head.get_center() + RIGHT * dx + UP * 0.06)
                    for dx in (-0.13, 0.13)])
    smile = Arc(radius=0.17, start_angle=PI + 0.6, angle=PI - 1.2, stroke_width=3, color=BG)
    smile.move_to(head.get_center() + DOWN * 0.1)
    parts = [body, head, eyes, smile]
    if bow:
        tie = Square(0.17, fill_color=MIST, fill_opacity=1, stroke_width=0).rotate(PI / 4)
        parts.append(tie.move_to(body.get_top() + DOWN * 0.1))
    if chef:
        hat = VGroup(
            RoundedRectangle(corner_radius=0.05, width=0.55, height=0.35, fill_color=MIST, fill_opacity=1, stroke_width=0),
            *[Circle(radius=0.2, fill_color=MIST, fill_opacity=1, stroke_width=0).shift(UP * 0.28 + RIGHT * dx)
              for dx in (-0.22, 0, 0.22)])
        parts.append(hat.next_to(head, UP, buff=-0.12))
    return VGroup(*parts).scale(1.4)


def to_floor(mob, x, floor):
    mob.move_to(RIGHT * x)
    mob.shift(UP * (floor - mob.get_bottom()[1]))
    return mob


class Restaurant(Scene):
    """Cartoon restaurant. mode "intro" events: customer, kitchen, waiter, order, meal
    mode "mapping" (everything already drawn) events: api, software, hide"""

    def construct(self):
        s = spec()
        mode = s.get("mode", "intro")
        floor = -1.3
        customer = to_floor(person(ORANGE), -4.8, floor)
        waiter = to_floor(person(BLUE, bow=True), 0, floor)
        chef = to_floor(person(GREEN, chef=True), 4.8, floor)
        box = RoundedRectangle(corner_radius=0.25, width=3.8, height=4.4, color=GREEN, fill_opacity=0.12)
        box.move_to(RIGHT * 4.8 + UP * 0.45)
        kitchen = VGroup(box, chef)

        def label(text, x):
            return T(text, font_size=30, color=MIST).move_to(RIGHT * x + DOWN * 2.5)

        labels = [label("You", -4.8), label("Waiter", 0), label("Kitchen", 4.8)]
        if s.get("title"):
            self.add(T(s["title"], font_size=40, color=MIST, weight=BOLD).to_edge(UP, buff=0.6))
        state = {}

        def appear(mob, lab):
            return lambda: (self.play(FadeIn(mob, shift=UP * 0.3), FadeIn(lab), run_time=0.6),
                            self.play(Indicate(mob, scale_factor=1.08), run_time=0.6))

        def order():
            bubble = VGroup(
                RoundedRectangle(corner_radius=0.2, width=2.5, height=0.8, fill_color=MIST, fill_opacity=1, stroke_width=0),
                T("Order, please!", font_size=22, color=BG))
            bubble[1].move_to(bubble[0])
            bubble.next_to(customer, UP, buff=0.15)
            slip = VGroup(Rectangle(width=0.45, height=0.6, fill_color=MIST, fill_opacity=1, stroke_width=0),
                          Line(LEFT * 0.14, RIGHT * 0.14, color=BG, stroke_width=3).shift(UP * 0.1),
                          Line(LEFT * 0.14, RIGHT * 0.14, color=BG, stroke_width=3).shift(DOWN * 0.08))
            slip.move_to(customer.get_right() + RIGHT * 0.4 + UP * 0.1)
            self.play(FadeIn(bubble, shift=UP * 0.2), run_time=0.4)
            self.play(FadeIn(slip), run_time=0.2)
            self.play(slip.animate.move_to(waiter.get_left() + LEFT * 0.4 + UP * 0.1), run_time=0.7)
            self.play(FadeOut(bubble), slip.animate.move_to(box.get_left() + RIGHT * 0.1 + UP * 0.1), run_time=0.8)
            self.play(FadeOut(slip), run_time=0.2)

        def meal():
            plate = VGroup(Circle(radius=0.3, fill_color=MIST, fill_opacity=1, stroke_width=0),
                           Dot(radius=0.13, color=ORANGE))
            plate.move_to(box.get_left() + RIGHT * 0.1 + UP * 0.1)
            self.play(FadeIn(plate, scale=0.5), run_time=0.3)
            self.play(plate.animate.move_to(waiter.get_right() + RIGHT * 0.4 + UP * 0.1), run_time=0.7)
            self.play(plate.animate.move_to(customer.get_right() + RIGHT * 0.4 + UP * 0.1), run_time=0.8)
            self.play(Indicate(customer, scale_factor=1.1), FadeOut(plate), run_time=0.5)

        def api():
            new = T("API", font_size=40, color=BLUE, weight=BOLD).move_to(labels[1])
            self.play(Transform(labels[1], new), Indicate(waiter, scale_factor=1.2, color=BLUE), run_time=1.0)

        def software():
            a = T("Your app", font_size=30, color=ORANGE).move_to(labels[0])
            b = T("Server", font_size=30, color=GREEN).move_to(labels[2])
            self.play(Transform(labels[0], a), Transform(labels[2], b), run_time=1.0)

        def hide():
            cover = VGroup(Rectangle(width=3.8, height=4.4, fill_color=BG, fill_opacity=0.92, stroke_width=0),
                           T("?", font_size=90, color=SOFT)).move_to(box)
            self.play(FadeIn(cover), run_time=0.8)

        if mode == "intro":
            run_events(self, {"customer": appear(customer, labels[0]), "kitchen": appear(kitchen, labels[2]),
                              "waiter": appear(waiter, labels[1]), "order": order, "meal": meal})
        else:
            self.add(customer, waiter, kitchen, *labels)
            run_events(self, {"api": api, "software": software, "hide": hide})
        hold_until_end(self)


# --------------------------------------------------------------------------- code
class CodeCard(Scene):
    def construct(self):
        s = spec()
        title = T(s.get("title", "Example"), font_size=40, color=MIST, weight=BOLD).to_edge(UP, buff=0.6)
        code = T(s.get("code", ""), font="Monospace", font_size=26, color=MIST, line_spacing=0.8)
        panel = RoundedRectangle(corner_radius=0.2, width=code.width + 0.8, height=code.height + 0.8,
                                 color=BLUE, fill_color="#161C2C", fill_opacity=1)
        block = fit(VGroup(panel, code.move_to(panel)), 12.0).next_to(title, DOWN, buff=0.5)
        self.play(FadeIn(title), FadeIn(block), run_time=0.8)

        def show_output():
            out = T(s.get("output", ""), font_size=28, color=GREEN).next_to(block, DOWN, buff=0.5)
            self.play(FadeIn(out, shift=UP * 0.2), Circumscribe(out, color=GREEN), run_time=1.0)

        if s.get("output"):
            run_events(self, {"output": show_output})
        hold_until_end(self)


# --------------------------------------------------------------------------- NLP templates
class Tokens(Scene):
    """A sentence splits into token chips, then each chip gets an id number.
    spec: sentence, tokens[], ids[], note.   events: split, ids"""

    def construct(self):
        s = spec()
        self.add(T(s.get("title", "Tokenization"), font_size=40, color=MIST, weight=BOLD).to_edge(UP, buff=0.6))
        sentence = T(s["sentence"], font_size=46, color=MIST).move_to(UP * 0.6)
        self.play(FadeIn(sentence), run_time=0.6)
        chips = VGroup()
        for tok in s["tokens"]:
            label = T(tok, font_size=54, color=MIST)
            box = RoundedRectangle(corner_radius=0.15, width=label.width + 0.8, height=1.3,
                                   color=BLUE, fill_opacity=0.25)
            chips.add(VGroup(box, label.move_to(box)))
        chips.arrange(RIGHT, buff=0.3)
        fit(chips, 12.6).move_to(UP * 0.6)

        def split():
            self.play(FadeOut(sentence), LaggedStart(*[FadeIn(c, scale=0.7) for c in chips], lag_ratio=0.2),
                      run_time=1.6)

        def ids():
            nums = VGroup(*[T(str(i), font="Monospace", font_size=42, color=ORANGE).next_to(c, DOWN, buff=0.5)
                            for c, i in zip(chips, s["ids"])])
            self.play(LaggedStart(*[FadeIn(n, shift=UP * 0.2) for n in nums], lag_ratio=0.2), run_time=1.6)
            if s.get("note"):
                self.play(FadeIn(T(s["note"], font_size=24, color=SOFT).to_edge(DOWN, buff=1.2)), run_time=0.6)

        run_events(self, {"split": split, "ids": ids})
        hold_until_end(self)


DEFAULT_CLUSTERS = [
    {"name": "animals", "color": "green", "words": ["cat", "dog", "lion"]},
    {"name": "vehicles", "color": "blue", "words": ["car", "truck", "bus"]},
    {"name": "food", "color": "orange", "words": ["pizza", "rice", "bread"]},
]


class WordMap(Scene):
    """Words as points on a 'map of meaning'; similar words cluster.
    spec: clusters[] (name, color, words[3]), note.   events: map, c0, c1, c2, note"""

    def construct(self):
        s = spec()
        clusters = s.get("clusters") or DEFAULT_CLUSTERS
        self.add(T(s.get("title", "A map of meaning"), font_size=40, color=MIST, weight=BOLD).to_edge(UP, buff=0.6))
        frame = RoundedRectangle(corner_radius=0.2, width=12.0, height=5.5, color=SOFT, stroke_opacity=0.5)
        frame.move_to(DOWN * 0.35)
        centers = [LEFT * 3.5 + UP * 0.7, RIGHT * 3.5 + UP * 0.7, DOWN * 1.65]
        offsets = [LEFT * 1.25 + UP * 0.35, RIGHT * 1.25 + UP * 0.45, DOWN * 0.55 + RIGHT * 0.1]

        def cluster_group(c, center):
            col = COLORS[c["color"]]
            dots = VGroup()
            for w, off in zip(c["words"], offsets):
                d = Dot(color=col, radius=0.16).move_to(center + off)
                lab = T(w, font_size=32, color=MIST).next_to(d, DOWN, buff=0.15)
                dots.add(VGroup(d, lab))
            ring = Ellipse(width=4.8, height=2.8, color=col, fill_color=col, fill_opacity=0.10).move_to(
                center + UP * 0.05)
            return ring, dots

        def show_map():
            self.play(Create(frame), run_time=0.9)

        def show_cluster(i):
            def go():
                ring, dots = cluster_group(clusters[i], centers[i])
                self.play(GrowFromCenter(ring), LaggedStart(*[FadeIn(d, scale=0.5) for d in dots], lag_ratio=0.25),
                          run_time=1.3)
                self.play(Indicate(ring, scale_factor=1.05), run_time=0.6)
            return go

        def show_note():
            note = T(s.get("note", "Real maps have hundreds or thousands of dimensions"), font_size=24, color=SOFT)
            self.play(FadeIn(note.move_to(DOWN * 3.5)), run_time=0.6)

        run_events(self, {"map": show_map, "c0": show_cluster(0), "c1": show_cluster(1),
                          "c2": show_cluster(2), "note": show_note})
        hold_until_end(self)


class Pipeline(Scene):
    """A chain of stages; a packet moves along as each stage is revealed.
    spec: stages[] (label, color).   events: s0, s1, s2, ..."""

    def construct(self):
        s = spec()
        stages = s.get("stages", [])
        if s.get("title"):
            self.add(T(s["title"], font_size=40, color=MIST, weight=BOLD).to_edge(UP, buff=0.6))
        n = len(stages)
        gap = 2.75
        xs = [(i - (n - 1) / 2) * gap for i in range(n)]
        boxes = [make_node(st["label"], COLORS[st["color"]], RIGHT * x + DOWN * 0.2) for st, x in zip(stages, xs)]
        for b in boxes:
            b[0].set_width(1.85)
            b[1].move_to(b[0])
        packet = Dot(color=ORANGE, radius=0.17)
        state = {}

        def reveal(i):
            def go():
                anims = [FadeIn(boxes[i], shift=UP * 0.2)]
                if i > 0:
                    anims.append(GrowArrow(Arrow(boxes[i - 1].get_right(), boxes[i].get_left(), buff=0.08, color=MIST)))
                self.play(*anims, run_time=0.6)
                target = boxes[i].get_top() + UP * 0.45
                if i == 0:
                    packet.move_to(target)
                    self.play(FadeIn(packet), run_time=0.3)
                else:
                    self.play(packet.animate.move_to(target), run_time=0.7)
                self.play(Indicate(boxes[i], scale_factor=1.1), run_time=0.5)
            return go

        run_events(self, {f"s{i}": reveal(i) for i in range(n)})
        hold_until_end(self)
