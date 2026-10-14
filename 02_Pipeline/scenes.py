"""Manim scene templates for Concept in Motion  (scenes.py)
=====================================================================
Each class below is one VISUAL TYPE you can use in a scenes json file:
  title, bullets, flow, restaurant, code, tokens, wordmap, pipeline, hub, agentloop, probbars, genloop, neuralnet, descent, losscurve
(the name-to-class table is CLASSES in build.py)

HOW build.py TALKS TO THIS FILE (environment variables set per scene)
  SCENE_SPEC     JSON of the scene's "visual" block from the scenes file
  SCENE_DURATION seconds of narration, so the animation can fill the audio exactly
  SCENE_CUES     JSON {event_name: seconds}, already shifted earlier so each visual lands
                 just BEFORE the words that name it. If a scene lists cues, ONLY the cued events run
                 (a template may offer more events than a scene uses). With no cues at all, events spread evenly.

HOW TO ADD A NEW VISUAL TYPE (e.g. "sorting")
  1. Write a class that extends Scene, read settings with spec(), and put each timed step in a
     function; then call run_events(self, {"event_name": function, ...}) and finish with
     hold_until_end(self).  Copy an existing class (Pipeline is the simplest) as a starting point.
  2. Register it in build.py:  CLASSES = {..., "sorting": "Sorting"}
  3. Use it in a scenes json:  "visual": {"type": "sorting", ...}, "cues": {"event_name": "exact phrase"}
  4. Test just that scene:  python build.py file.json --preview --only N

BRAND RULES (keep every video consistent)
  blue = data / API,  orange = user / packet,  green = server,  dark navy background, Poppins font.
  Keep important visuals out of the bottom-right corner (the channel watermark lives there).

FONT NOTE: if Manim prints "couldn't load font Poppins", install Poppins "for all users" on Windows and
restart PowerShell, or set FONT = None below to use the system font.
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
    """actions: {name: function}. Each runs at its cue time. If a scene has NO cues at all, every event is spread evenly.
    If a scene has cues, only the events that have a cue run (so a template can offer more events than a scene uses)."""
    c, names, timed = cues(), list(actions), []
    if c:                                   # a scene that lists cues runs ONLY those events
        names = [n for n in names if n in c]
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


# --------------------------------------------------------------------------- AI-agent templates
class Hub(Scene):
    """A centre node with satellites that appear one by one (parts of a system, tools around an agent...).
    spec: title, center (label), items[] (label, sub, color) with 1 to 4 items.
    events: center, n0, n1, n2, n3  (satellite order: left, right, bottom, top)"""

    def construct(self):
        s = spec()
        items = s.get("items", [])
        if s.get("title"):
            self.add(T(s["title"], font_size=40, color=MIST, weight=BOLD).to_edge(UP, buff=0.6))
        center = make_node(s.get("center", "Centre"), COLORS[s.get("center_color", "orange")], UP * -0.15)
        center[0].set_width(3.2)
        center[1].move_to(center[0])
        slots = [LEFT * 4.8 + DOWN * 0.15, RIGHT * 4.8 + DOWN * 0.15, DOWN * 2.5, UP * 2.05]
        default_cols = ["blue", "green", "blue", "green"]
        sats, lines = [], []
        for i, it in enumerate(items[:4]):
            col = COLORS[it.get("color", default_cols[i])]
            box = RoundedRectangle(corner_radius=0.2, width=3.7, height=1.35, color=col, fill_opacity=0.22)
            label = T(it["label"], font_size=30, color=MIST, weight=BOLD)
            sub = T(it.get("sub", ""), font_size=20, color=SOFT)
            txt = VGroup(label, sub).arrange(DOWN, buff=0.12)
            fit(txt, 3.3).move_to(box)
            sat = VGroup(box, txt).move_to(slots[i])
            sats.append(sat)
            d = [LEFT, RIGHT, DOWN, UP][i]               # connect facing edges, never through the labels
            lines.append(Line(center.get_edge_center(d), sat.get_edge_center(-d), color=col,
                              stroke_width=4, stroke_opacity=0.8))
        for ln in lines:
            ln.set_z_index(-1)
        center.set_z_index(2)

        def show_center():
            self.play(FadeIn(center, scale=0.6), run_time=0.6)
            self.play(Indicate(center, scale_factor=1.1), run_time=0.5)

        def show_sat(i):
            def go():
                self.play(Create(lines[i]), FadeIn(sats[i], scale=0.6), run_time=0.8)
                self.play(Indicate(sats[i], scale_factor=1.08), run_time=0.5)
            return go

        acts = {"center": show_center}
        acts.update({f"n{i}": show_sat(i) for i in range(len(sats))})
        run_events(self, acts)
        hold_until_end(self)


class AgentLoop(Scene):
    """The agent loop: Think -> Act -> Observe -> repeat.
    spec: title, goal, log[] of {stage: think|act|observe, text}.
    No log:  events think, act, observe, repeat, done          (explains the loop)
    With log: events l0, l1, l2, ..., done                       (a worked example, one log line per step)"""
    INFO = {"think": ("Think", "Decide the next step", BLUE),
            "act": ("Act", "Use a tool", ORANGE),
            "observe": ("Observe", "Read the result", GREEN)}

    def construct(self):
        s = spec()
        log = s.get("log")
        if s.get("title"):
            self.add(T(s["title"], font_size=40, color=MIST, weight=BOLD).to_edge(UP, buff=0.6))
        if log:
            pos = {"think": LEFT * 5.0 + UP * 0.9, "act": LEFT * 0.9 + UP * 0.9, "observe": LEFT * 2.95 + DOWN * 1.9}
        else:
            pos = {"think": LEFT * 3.8 + UP * 0.9, "act": RIGHT * 3.8 + UP * 0.9, "observe": DOWN * 2.0}
        nodes = {}
        for key, (name, sub, col) in self.INFO.items():
            box = RoundedRectangle(corner_radius=0.2, width=2.7, height=1.5, color=col, fill_opacity=0.25)
            label = T(name, font_size=32, color=MIST, weight=BOLD)
            hint = T(sub, font_size=20, color=SOFT)
            txt = VGroup(label, hint).arrange(DOWN, buff=0.12)
            fit(txt, 2.4).move_to(box)
            nodes[key] = VGroup(box, txt).scale(1.0 if log else 1.3).move_to(pos[key])
        arrows = [Arrow(nodes["think"], nodes["act"], buff=0.15, color=MIST, stroke_width=5),
                  Arrow(nodes["act"], nodes["observe"], buff=0.15, color=MIST, stroke_width=5),
                  Arrow(nodes["observe"], nodes["think"], buff=0.15, color=MIST, stroke_width=5)]
        packet = Dot(color=ORANGE, radius=0.18)
        above = lambda k: nodes[k].get_top() + UP * 0.42
        state = {"packet_on": False}

        def move_packet(key):
            if not state["packet_on"]:
                packet.move_to(above(key))
                self.play(FadeIn(packet), run_time=0.3)
                state["packet_on"] = True
            else:
                self.play(packet.animate.move_to(above(key)), run_time=0.7)

        if not log:
            def stage(key, arrow=None):
                def go():
                    anims = [FadeIn(nodes[key], scale=0.7)]
                    if arrow is not None:
                        anims.append(GrowArrow(arrow))
                    self.play(*anims, run_time=0.6)
                    move_packet(key)
                    self.play(Indicate(nodes[key], scale_factor=1.1), run_time=0.5)
                return go

            centre = (nodes["think"].get_center() + nodes["act"].get_center() + nodes["observe"].get_center()) / 3
            texts = {}

            def repeat():
                self.play(GrowArrow(arrows[2]), run_time=0.6)
                move_packet("think")
                texts["r"] = T("Repeat", font_size=38, color=SOFT).move_to(centre + UP * 0.2)
                self.play(FadeIn(texts["r"]), run_time=0.5)

            def done():
                finish = T("Goal done", font_size=44, color=GREEN, weight=BOLD).move_to(centre + UP * 0.2)
                outs = [FadeOut(packet)]
                if "r" in texts:
                    outs.append(FadeOut(texts["r"]))
                self.play(*outs, FadeIn(finish, scale=0.8), run_time=0.8)

            run_events(self, {"think": stage("think"), "act": stage("act", arrows[0]),
                              "observe": stage("observe", arrows[1]), "repeat": repeat, "done": done})
        else:
            self.add(*nodes.values(), *arrows)
            x0 = 1.15
            head = T("What the agent does", font_size=24, color=SOFT)
            head.move_to(RIGHT * x0 + UP * 2.3, aligned_edge=LEFT)
            goal = T("Goal: " + s.get("goal", ""), font_size=24, color=MIST)
            fit(goal, 5.7).move_to(RIGHT * x0 + UP * 1.8, aligned_edge=LEFT)
            self.add(head, goal)

            def step(i, item):
                def go():
                    key = item["stage"]
                    move_packet(key)
                    name, _, col = self.INFO[key]
                    line = T(f"{name}: {item['text']}", font_size=21, color=col)
                    fit(line, 5.7).move_to(RIGHT * x0 + UP * (1.2 - i * 0.46), aligned_edge=LEFT)
                    self.play(Indicate(nodes[key], scale_factor=1.1), FadeIn(line, shift=RIGHT * 0.2), run_time=0.7)
                return go

            def done():
                finish = T(s.get("done_text", "Goal done"), font_size=36, color=GREEN, weight=BOLD)
                finish.move_to(RIGHT * x0 + DOWN * 3.0, aligned_edge=LEFT)
                self.play(FadeOut(packet), FadeIn(finish, scale=0.8), run_time=0.8)

            acts = {f"l{i}": step(i, it) for i, it in enumerate(log)}
            acts["done"] = done
            run_events(self, acts)
        hold_until_end(self)


# --------------------------------------------------------------------------- LLM next-word templates
class ProbBars(Scene):
    """Probabilities for the next word, drawn as bars.
    spec: title, prompt, bars[] (word, p), more, note, mode (build|pick), pick (a word from bars), temp.
    build mode events: prompt, b0, b1, b2, ...,  note
    pick mode (bars already on screen): pick, temp"""

    def construct(self):
        s = spec()
        mode = s.get("mode", "build")
        bars = s.get("bars", [])
        if s.get("title"):
            self.add(T(s["title"], font_size=40, color=MIST, weight=BOLD).to_edge(UP, buff=0.6))
        prompt = T(s.get("prompt", ""), font_size=46, color=MIST)
        blank = T("?", font_size=46, color=SOFT)
        head = VGroup(prompt, blank).arrange(RIGHT, buff=0.3).move_to(UP * 1.95)
        top = max(b["p"] for b in bars) if bars else 1
        rows = []
        for i, b in enumerate(bars):
            y = 0.7 - i * 0.98
            word = T(b["word"], font_size=38, color=MIST).move_to(LEFT * 2.2 + UP * y, aligned_edge=RIGHT)
            bar = Rectangle(width=max(b["p"] / top * 5.4, 0.08), height=0.6, fill_color=BLUE, fill_opacity=1,
                            stroke_width=0).move_to(LEFT * 1.9 + UP * y, aligned_edge=LEFT)
            pct = T(f"{b['p']}%", font_size=32, color=SOFT).next_to(bar, RIGHT, buff=0.2)
            rows.append(VGroup(word, bar, pct))
        extra = T(s.get("more", ""), font_size=26, color=SOFT).move_to(DOWN * 3.0)
        note = T(s.get("note", ""), font_size=24, color=SOFT).move_to(DOWN * 3.5)

        def show_prompt():
            self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.7)

        def show_bar(i):
            def go():
                w, bar, pct = rows[i]
                self.play(FadeIn(w), GrowFromEdge(bar, LEFT), run_time=0.8)
                self.play(FadeIn(pct), run_time=0.3)
            return go

        def show_note():
            self.play(FadeIn(extra), FadeIn(note), run_time=0.6)

        def pick():
            word = s.get("pick") or bars[0]["word"]
            idx = [b["word"] for b in bars].index(word)
            w, bar, pct = rows[idx]
            chosen = T(word, font_size=46, color=ORANGE).next_to(prompt, RIGHT, buff=0.3)
            self.play(bar.animate.set_fill(ORANGE), Indicate(w, color=ORANGE), run_time=0.7)
            self.play(FadeOut(blank), ReplacementTransform(w.copy(), chosen), run_time=0.9)

        def temp():
            t = T(s.get("temp", "Temperature: low = safe, high = varied"), font_size=30, color=MIST)
            self.play(FadeIn(t.move_to(DOWN * 3.3), shift=UP * 0.2), run_time=0.7)

        if mode == "build":
            acts = {"prompt": show_prompt}
            acts.update({f"b{i}": show_bar(i) for i in range(len(rows))})
            acts["note"] = show_note
            run_events(self, acts)
        else:
            self.add(head, *rows, extra)
            run_events(self, {"pick": pick, "temp": temp})
        hold_until_end(self)


class GenLoop(Scene):
    """A sentence grows one predicted word at a time.
    spec: title, prompt, words[], label.   events: label, w0, w1, ..."""

    def construct(self):
        s = spec()
        words = s.get("words", [])
        if s.get("title"):
            self.add(T(s["title"], font_size=40, color=MIST, weight=BOLD).to_edge(UP, buff=0.6))
        model = make_node("LLM", BLUE, UP * 1.5)
        model[0].set_width(3.0)
        model[1].become(T("LLM", font_size=40, color=MIST, weight=BOLD).move_to(model[0]))
        self.add(model)
        base = s.get("prompt", "")
        state = {"cur": T(base, font_size=50, color=MIST).move_to(DOWN * 0.6)}
        self.add(state["cur"])

        def add_word(i, w):
            def go():
                full = base + " " + " ".join(words[:i + 1])
                start = len(full) - len(w)        # colour only the newest word, keep one baseline for the line
                new = T(full, font_size=50, color=MIST, t2c={f"[{start}:{len(full)}]": ORANGE}).move_to(DOWN * 0.6)
                arrow = Arrow(model.get_bottom(), new.get_right() + LEFT * 0.7 + UP * 0.5, buff=0.1,
                              color=ORANGE, stroke_width=5)
                self.play(ReplacementTransform(state["cur"], new), GrowArrow(arrow),
                          Indicate(model, scale_factor=1.12), run_time=0.9)
                self.play(FadeOut(arrow), run_time=0.3)
                state["cur"] = new
            return go

        def label():
            t = T(s.get("label", "Predict, add, repeat"), font_size=44, color=SOFT, weight=BOLD).move_to(DOWN * 2.3)
            self.play(FadeIn(t, shift=UP * 0.2), run_time=0.7)

        acts = {"label": label}
        acts.update({f"w{i}": add_word(i, w) for i, w in enumerate(words)})
        run_events(self, acts)
        hold_until_end(self)


# --------------------------------------------------------------------------- neural-network templates
class NeuralNet(Scene):
    """A layered network: signal flows forward, error flows back, weights change.
    spec: title, layers[] (default 3,4,4,2), input_label, outputs[], guess[], after[], error_text,
          pre[] = things already on screen: nodes, weights, lit, guess, error
    events: input, hidden, output, weights, signal, answer, error, adjust, done"""

    def construct(self):
        import random
        rng = random.Random(7)
        s = spec()
        sizes = s.get("layers", [3, 4, 4, 2])
        outputs = s.get("outputs", ["cat", "dog"])
        guess = s.get("guess", ["cat 30%", "dog 70%"])
        after = s.get("after", ["cat 45%", "dog 55%"])
        pre = set(s.get("pre", []))
        if s.get("title"):
            self.add(T(s["title"], font_size=40, color=MIST, weight=BOLD).to_edge(UP, buff=0.6))
        xs = np.linspace(-3.4, 3.0, len(sizes))
        layers = []
        for x, k in zip(xs, sizes):
            layer = VGroup(*[Circle(radius=0.3, stroke_color=BLUE, stroke_width=4, fill_color="#1B2438",
                                    fill_opacity=1).move_to(RIGHT * x + UP * (((k - 1) / 2 - j) * 1.1 - 0.1))
                             for j in range(k)])
            layers.append(layer)
        for layer in layers:
            layer.set_z_index(2)
        lines, widths = [], []
        for a, b in zip(layers[:-1], layers[1:]):
            for na in a:
                for nb in b:
                    w = rng.uniform(0.15, 1.0)
                    ln = Line(na.get_center(), nb.get_center(), color=MIST, stroke_width=1.2 + 4.5 * w,
                              stroke_opacity=0.2 + 0.6 * w)
                    ln.set_z_index(0)
                    lines.append(ln)
        lines = VGroup(*lines)
        in_label = T(s.get("input_label", "Photo of a cat"), font_size=24, color=SOFT)
        in_label.next_to(layers[0], LEFT, buff=0.5)
        out_names = [T(o, font_size=34, color=MIST).next_to(n, RIGHT, buff=0.4) for o, n in zip(outputs, layers[-1])]
        out_guess = [T(g, font_size=34, color=MIST).next_to(n, RIGHT, buff=0.4) for g, n in zip(guess, layers[-1])]
        out_after = [T(g, font_size=34, color=GREEN).next_to(n, RIGHT, buff=0.4) for g, n in zip(after, layers[-1])]
        state = {"out": out_guess if "guess" in pre else out_names}
        note_pos = DOWN * 3.1

        if "nodes" in pre:
            self.add(*layers, in_label, *state["out"])
        if "weights" in pre:
            self.add(lines)
        if "lit" in pre:
            for layer in layers:
                layer.set_fill(ORANGE, 1)
        if "guess" in pre and "nodes" not in pre:
            self.add(*state["out"])
        if "error" in pre:
            self.add(T(s.get("error_text", "Label: cat. The guess was wrong"), font_size=30, color=ORANGE).move_to(note_pos))

        def show_input():
            self.play(LaggedStart(*[FadeIn(n, scale=0.5) for n in layers[0]], lag_ratio=0.2), FadeIn(in_label), run_time=1.0)

        def show_hidden():
            mids = [n for layer in layers[1:-1] for n in layer]
            self.play(LaggedStart(*[FadeIn(n, scale=0.5) for n in mids], lag_ratio=0.08), run_time=1.3)

        def show_output():
            self.play(LaggedStart(*[FadeIn(n, scale=0.5) for n in layers[-1]], lag_ratio=0.2),
                      *[FadeIn(t) for t in state["out"]], run_time=1.0)

        def show_weights():
            self.play(Create(lines, lag_ratio=0.02), run_time=1.6)
            self.play(FadeIn(T("Thicker line = stronger weight", font_size=28, color=SOFT).move_to(note_pos)), run_time=0.6)

        def signal():
            for layer in layers:
                self.play(*[n.animate.set_fill(ORANGE, 1) for n in layer], run_time=0.45)

        def answer():
            self.play(*[ReplacementTransform(a, b) for a, b in zip(state["out"], out_guess)], run_time=0.8)
            state["out"] = out_guess

        def error():
            t = T(s.get("error_text", "Label: cat. The guess was wrong"), font_size=30, color=ORANGE).move_to(note_pos)
            self.play(FadeIn(t, shift=UP * 0.2), run_time=0.7)

        def adjust():
            self.play(LaggedStart(*[AnimationGroup(*[n.animate.set_fill(GREEN, 1) for n in layer])
                                    for layer in reversed(layers)], lag_ratio=0.6), run_time=1.8)
            anims = [ln.animate.set_stroke(width=1.2 + 4.5 * rng.uniform(0.15, 1.0), opacity=0.2 + 0.6 * rng.uniform(0.2, 1))
                     for ln in lines]
            anims += [n.animate.set_fill("#1B2438", 1) for layer in layers for n in layer]
            self.play(*anims, run_time=1.2)

        def done():
            self.play(*[ReplacementTransform(a, b) for a, b in zip(state["out"], out_after)], run_time=0.8)
            state["out"] = out_after

        run_events(self, {"input": show_input, "hidden": show_hidden, "output": show_output, "weights": show_weights,
                          "signal": signal, "answer": answer, "error": error, "adjust": adjust, "done": done})
        hold_until_end(self)


class Descent(Scene):
    """A ball rolls down a valley in shrinking steps (gradient descent).
    events: valley, ball, steps, label, name, rate"""

    def construct(self):
        s = spec()
        if s.get("title"):
            self.add(T(s["title"], font_size=40, color=MIST, weight=BOLD).to_edge(UP, buff=0.6))
        f = lambda x: 0.17 * x ** 2 - 2.1
        curve = ParametricFunction(lambda t: np.array([t, f(t), 0]), t_range=[-5.2, 5.2], color=SOFT, stroke_width=6)
        pt = lambda x: np.array([x, f(x) + 0.27, 0])
        ball = Dot(radius=0.26, color=ORANGE).move_to(pt(-4.5))
        stops = [-4.5, -3.3, -2.3, -1.5, -0.9, -0.45, -0.1]

        def valley():
            self.play(Create(curve), run_time=1.4)

        def show_ball():
            self.play(FadeIn(ball, scale=0.5), run_time=0.5)

        def steps():
            for a, b in zip(stops[:-1], stops[1:]):
                mark = Dot(radius=0.07, color=MIST).move_to(np.array([a, f(a) + 0.05, 0]))
                self.play(FadeIn(mark), ball.animate.move_to(pt(b)), run_time=0.55)

        def label():
            self.play(FadeIn(T("Height = error", font_size=32, color=ORANGE).move_to(UP * 1.5)), run_time=0.6)

        def name():
            self.play(FadeIn(T("Gradient descent", font_size=36, color=MIST, weight=BOLD).move_to(DOWN * 2.9)), run_time=0.7)

        def rate():
            self.play(FadeIn(T("Step size = learning rate", font_size=30, color=SOFT).move_to(DOWN * 3.5)), run_time=0.7)

        run_events(self, {"valley": valley, "ball": show_ball, "steps": steps, "label": label, "name": name, "rate": rate})
        hold_until_end(self)


class LossCurve(Scene):
    """Error falling over practice rounds.   events: axes, curve, test"""

    def construct(self):
        import random
        rng = random.Random(3)
        s = spec()
        if s.get("title"):
            self.add(T(s["title"], font_size=40, color=MIST, weight=BOLD).to_edge(UP, buff=0.6))
        x0, y0 = -5.0, -2.2
        xaxis = Arrow(np.array([x0, y0, 0]), np.array([5.6, y0, 0]), buff=0, color=MIST, stroke_width=4)
        yaxis = Arrow(np.array([x0, y0, 0]), np.array([x0, 2.4, 0]), buff=0, color=MIST, stroke_width=4)
        xl = T("Practice rounds", font_size=28, color=SOFT).next_to(xaxis, DOWN, buff=0.2)
        yl = T("Error", font_size=28, color=SOFT).next_to(yaxis, UP, buff=0.15)
        pts = []
        for i in range(61):
            t = i / 60
            err = 0.1 + 0.95 * np.exp(-3.4 * t) + rng.uniform(-0.04, 0.04) * (1 - t * 0.6)
            pts.append(np.array([x0 + 0.3 + t * 10.0, y0 + 0.2 + 3.1 * err, 0]))
        curve = VMobject(color=GREEN, stroke_width=6).set_points_smoothly(pts)
        dot = Dot(radius=0.16, color=ORANGE).move_to(pts[0])

        def axes():
            self.play(Create(xaxis), Create(yaxis), FadeIn(xl), FadeIn(yl), run_time=1.0)

        def draw():
            self.add(dot)
            self.play(Create(curve), MoveAlongPath(dot, curve), run_time=3.0, rate_func=linear)

        def test():
            self.play(FadeIn(T("Then test on new examples it has never seen", font_size=30, color=GREEN).move_to(UP * 2.1 + RIGHT * 0.8)),
                      run_time=0.8)

        run_events(self, {"axes": axes, "curve": draw, "test": test})
        hold_until_end(self)
