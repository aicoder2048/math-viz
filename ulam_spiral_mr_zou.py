import colorsys
import math
import os
import random
import sys
import time
import turtle
import argparse


def is_prime(n):
    """判断是否为质数"""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def is_sophie_germain(n):
    """判断是否为 Sophie Germain 质数 (p 和 2p+1 都是质数)"""
    return is_prime(n) and is_prime(2 * n + 1)


def is_palindrome(n):
    """判断是否为回文数"""
    s = str(n)
    return s == s[::-1]


def get_color_for_prime(n, index):
    """根据质数大小返回丰富的渐变色 - 使用HSL色彩空间"""
    import colorsys

    # 使用HSL色彩空间生成丰富的颜色
    # 色相从0到1循环，饱和度保持高，亮度适中
    hue = (index * 0.618) % 1.0  # 黄金比例分布色相
    saturation = 0.75 + (index % 3) * 0.08  # 75%-91% 饱和度
    lightness = 0.55 + (index % 4) * 0.05   # 55%-70% 亮度

    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))


def get_contrast_text_color(bg_color_hex):
    """根据背景色自动返回对比度最高的文字颜色（黑或白）"""
    # 解析十六进制颜色
    bg_color_hex = bg_color_hex.lstrip('#')
    r = int(bg_color_hex[0:2], 16)
    g = int(bg_color_hex[2:4], 16)
    b = int(bg_color_hex[4:6], 16)

    # 计算亮度 (YIQ 公式，更符合人眼感知)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

    # 亮度高用黑字，亮度低用白字
    return "black" if luminance > 0.5 else "white"


SF2_PATH = os.path.join(os.path.dirname(__file__), "FluidR3_GM.sf2")

# 可选调式 (每个调式6个音，prime%6 映射 0-5 无盲区)
SCALE_POOL = {
    "大调（明亮）":     [0, 2, 4, 7, 9, 11],   # C D E G A B
    "小调（忧郁）":     [0, 2, 3, 7, 8, 11],   # C D Eb G Ab B
    "多利亚（古典）":   [0, 2, 3, 5, 7, 10],   # C D Eb F G Bb
    "混合吕底亚（爵士）": [0, 2, 4, 7, 9, 10], # C D E G A Bb
    "五声音阶（东方）": [0, 2, 4, 7, 9, 12],   # C D E G A C'
    "布鲁斯（蓝调）":   [0, 3, 5, 6, 7, 10],   # C Eb F F# G Bb
}

# 风格/调式配色
STYLE_COLORS = {
    "月光": "#b0c4de",   # 淡钢蓝
    "晨曦": "#f0c060",   # 暖金
    "夜想": "#9b8ec4",   # 薰衣草紫
    "田园": "#8fbc8f",   # 草绿
    "冥想": "#c4a882",   # 檀香棕
}
SCALE_COLORS = {
    "大调（明亮）":       "#f5d76e",  # 明黄
    "小调（忧郁）":       "#a8b4d4",  # 雾蓝
    "多利亚（古典）":     "#c9a96e",  # 古铜
    "混合吕底亚（爵士）": "#e8a87c",  # 暖橘
    "五声音阶（东方）":   "#d4a5a5",  # 胭脂粉
    "布鲁斯（蓝调）":     "#7eb8c9",  # 蓝调青
}

# 风格套装: 只用钢琴(0,1) + 竖琴(46) + 弦乐伴奏(48)
# ch0=普通质数(钢琴), ch1=孪生(钢琴), ch2=表兄弟(竖琴), ch3=性感(弦乐), ch4=弦乐铺底
STYLE_PRESETS = [
    {
        "name": "月光",
        "scales": ["小调（忧郁）", "大调（明亮）"],
        "instruments": [0, 0, 46, 48, 48],     # Piano, Piano, Harp, Strings, Strings
        "base": 60,
    },
    {
        "name": "晨曦",
        "scales": ["大调（明亮）", "五声音阶（东方）"],
        "instruments": [0, 1, 46, 48, 48],     # Piano, BrightPiano, Harp, Strings, Strings
        "base": 60,
    },
    {
        "name": "夜想",
        "scales": ["小调（忧郁）", "多利亚（古典）"],
        "instruments": [0, 0, 46, 48, 48],     # Piano, Piano, Harp, Strings, Strings
        "base": 60,
    },
    {
        "name": "田园",
        "scales": ["大调（明亮）", "混合吕底亚（爵士）"],
        "instruments": [1, 0, 46, 48, 48],     # BrightPiano, Piano, Harp, Strings, Strings
        "base": 60,
    },
    {
        "name": "冥想",
        "scales": ["五声音阶（东方）", "小调（忧郁）"],
        "instruments": [0, 0, 46, 48, 48],     # Piano, Piano, Harp, Strings, Strings
        "base": 60,
    },
]


def init_sound():
    """初始化 FluidSynth，随机选择风格套装"""
    import random
    # macOS homebrew: 确保 pyfluidsynth 能找到 libfluidsynth
    if "/opt/homebrew/lib" not in os.environ.get("DYLD_LIBRARY_PATH", ""):
        os.environ["DYLD_LIBRARY_PATH"] = "/opt/homebrew/lib:" + os.environ.get("DYLD_LIBRARY_PATH", "")
    import fluidsynth
    fs = fluidsynth.Synth(gain=0.4)
    fs.start(driver="coreaudio")
    sfid = fs.sfload(SF2_PATH)

    # 轻柔混响（试听第三部分选项1的参数）
    fs.set_reverb(roomsize=0.15, damping=0.8, width=0.3, level=0.1)
    # 关闭合唱效果
    fs.setting("synth.chorus.active", 0)

    # 随机选风格
    style = random.choice(STYLE_PRESETS)
    scale_name = random.choice(style["scales"])
    scale = SCALE_POOL[scale_name]
    base_note = style["base"]

    # ch0-ch3: 旋律乐器, ch4: 低音弦乐铺底
    for ch in range(5):
        fs.program_select(ch, sfid, 0, style["instruments"][ch])

    # 预计算 MIDI 音高矩阵 — 只用2个八度 (C4-C5 范围，温柔不刺耳)
    note_map = []
    for octave in range(2):
        note_map.append([base_note + octave * 12 + s for s in scale])

    config_info = {
        "scale": scale_name,
        "style": style["name"],
    }
    return fs, note_map, config_info


def get_spiral_position(index):
    """
    获取第 index 个位置（从0开始）在螺旋中的相对坐标
    index=0 -> (0,0), index=1 -> (1,0), index=2 -> (1,1), ...
    """
    if index == 0:
        return (0, 0)

    # 找到当前所在的层
    layer = 1
    while True:
        # 第 layer 层结束时的索引 (2*layer+1)^2 - 1
        max_index = (2 * layer + 1) ** 2 - 1
        if index <= max_index:
            break
        layer += 1

    # 在当前层中的位置 (0-based within layer)
    prev_max = (2 * (layer - 1) + 1) ** 2 - 1 if layer > 0 else 0
    pos_in_layer = index - prev_max - 1

    # 当前层的边长
    side_len = 2 * layer

    # 确定在哪一条边上 (0=右, 1=上, 2=左, 3=下)
    side = pos_in_layer // side_len
    pos_in_side = pos_in_layer % side_len

    # 计算坐标
    if side == 0:  # 右边 (从下往上)
        x = layer
        y = -layer + 1 + pos_in_side
    elif side == 1:  # 上边 (从右往左)
        x = layer - 1 - pos_in_side
        y = layer
    elif side == 2:  # 左边 (从上往下)
        x = -layer
        y = layer - 1 - pos_in_side
    else:  # 下边 (从左往右)
        x = -layer + 1 + pos_in_side
        y = -layer

    return (x, y)


def draw_ulam_spiral(total_numbers=None, size="mid", start_num=1, sound=False, paused=False, fireworks=False):
    """绘制乌拉姆螺旋 - 质数用不同颜色表示

    Args:
        total_numbers: 要绘制的数字总数，默认根据size自动选择
        size: 窗口尺寸 ('small', 'mid', 'large')
        start_num: 起始数字，默认从1开始
        sound: 是否开启质数音效
        paused: 是否以暂停状态启动
    """
    # 尺寸配置 (包含默认数字数量)
    size_configs = {
        "small": {"width": 800, "height": 600, "cell_size": 28, "radius": 12, "font": 8, "default_count": 200},
        "mid": {"width": 1400, "height": 900, "cell_size": 32, "radius": 14, "font": 10, "default_count": 500},
        "large": {"width": 1800, "height": 1000, "cell_size": 28, "radius": 12, "font": 9, "default_count": 1200},
    }

    config = size_configs.get(size, size_configs["mid"])
    width = config["width"]
    height = config["height"]
    cell_size = config["cell_size"]
    circle_radius = config["radius"]
    font_size = config["font"]

    # 如果未指定数量，使用size对应的默认值
    if total_numbers is None:
        total_numbers = config["default_count"]

    # 初始化 FluidSynth 音效
    synth = note_map = sound_config = None
    if sound:
        try:
            synth, note_map, sound_config = init_sound()
            print(f"Music: {sound_config['style']} · {sound_config['scale']}")
        except Exception as e:
            print(f"音效初始化失败: {e}")

    # 创建画布
    screen = turtle.Screen()
    screen.title(f"Ulam Spiral - Prime Numbers (start={start_num}, count={total_numbers}, size={size})")
    screen.bgcolor("#0a0a0a")  # 深黑背景
    screen.setup(width=width, height=height)

    # 窗口置顶
    screen._root.attributes("-topmost", True)

    # 关闭自动刷新，手动控制每帧显示
    screen.tracer(0)

    # 创建画笔
    t = turtle.Turtle()
    t.speed(0)
    t.hideturtle()

    # 面板通用字体
    PANEL_FONT = "PingFang SC"

    # --- 辅助函数：画圆角矩形背景卡片 ---
    def draw_card(pen, x, y, w, h, bg="#151518", border="#333333"):
        """在 (x, y) 左下角画一个带边框的矩形卡片"""
        r = 8  # 圆角半径
        pen.penup()
        pen.goto(x + r, y)
        pen.pendown()
        pen.color(border, bg)
        pen.pensize(1)
        pen.begin_fill()
        # 下边
        pen.forward(w - 2 * r)
        pen.circle(r, 90)
        # 右边
        pen.forward(h - 2 * r)
        pen.circle(r, 90)
        # 上边
        pen.forward(w - 2 * r)
        pen.circle(r, 90)
        # 左边
        pen.forward(h - 2 * r)
        pen.circle(r, 90)
        pen.end_fill()
        pen.penup()

    # --- 统计面板 ---
    stats_t = turtle.Turtle()
    stats_t.speed(0)
    stats_t.hideturtle()
    stats_t.penup()
    STATS_W = 230
    STATS_H = 390
    stats_x = width // 2 - STATS_W - 20   # 右侧留 20px 边距
    stats_y = height // 2 - 20             # 顶部留 20px
    stats_content_x = stats_x + 18         # 文字左边距
    stats_content_y = stats_y - 28         # 文字起始 y

    # --- 百科面板 ---
    info_t = turtle.Turtle()
    info_t.speed(0)
    info_t.hideturtle()
    info_t.penup()

    INFO_CONTENT = [
        ("质数 Prime", "#ffffff", [
            ("定义", "只能被 1 和自身整除的大于 1 的自然数"),
            ("应用", "RSA 加密算法的基石，守护互联网安全"),
        ]),
        ("孪生质数 Twin · gap = 2", "#ffd700", [
            ("定义", "差为 2 的质数对，如 (3,5) (11,13) (29,31)"),
            ("未解之谜", "是否有无穷多对？至今未证明！"),
            ("里程碑", "2013 年张益唐证明存在无穷多对差 < 7000 万的质数对"),
        ]),
        ("表兄弟质数 Cousin · gap = 4", "#00e5ff", [
            ("定义", "差为 4 的质数对，如 (3,7) (7,11) (13,17)"),
            ("趣事", "比孪生质数更常见，但同样不知道是否无穷多"),
        ]),
        ("性感质数 Sexy · gap = 6", "#ff69b4", [
            ("定义", "差为 6 的质数对，名字来自拉丁语 sex（六）"),
            ("趣事", "可形成三胞胎 (5,11,17) 甚至四胞胎 (5,11,17,23)！"),
        ]),
        ("◆ 安全质数 Sophie Germain", "#aaaaaa", [
            ("定义", "p 和 2p+1 都是质数，如 2, 3, 5, 11, 23, 29"),
            ("应用", "Diffie-Hellman 密钥交换的核心，网银安全的基础"),
        ]),
        ("★ 回文质数 Palindrome", "#aaaaaa", [
            ("定义", "正读反读都一样的质数，如 131, 151, 797"),
            ("趣事", "除了 11，所有回文质数都是奇数位数（想想为什么？）"),
        ]),
    ]

    PAD = 24          # 卡片内边距
    INFO_W = 540
    INFO_H = 620
    info_box_x = -width // 2 + 30
    info_box_y = height // 2 - 10

    def _draw_separator(y):
        """画一条淡色分隔线"""
        info_t.goto(info_box_x + PAD, y + 4)
        info_t.pendown()
        info_t.color("#2a2a2a")
        info_t.forward(INFO_W - PAD * 2)
        info_t.penup()

    def toggle_info():
        """按 i 键展开/收起质数百科"""
        if state.get("info_shown"):
            info_t.clear()
            state["info_shown"] = False
        else:
            info_t.clear()
            draw_card(info_t, info_box_x, info_box_y - INFO_H, INFO_W, INFO_H,
                      bg="#111114", border="#2a2a2a")

            y = info_box_y - 40
            info_t.goto(info_box_x + PAD, y)
            info_t.color("#ffffff")
            info_t.write("质 数 百 科", font=(PANEL_FONT, 18, "bold"))
            y -= 20
            _draw_separator(y)
            y -= 16

            for idx, (title, color, details) in enumerate(INFO_CONTENT):
                # 标题行
                info_t.goto(info_box_x + PAD, y)
                info_t.color(color)
                info_t.write(title, font=(PANEL_FONT, 12, "bold"))
                y -= 22

                # 详情（缩进，标签+内容）
                for label, text in details:
                    info_t.goto(info_box_x + PAD + 12, y)
                    info_t.color("#888888")
                    info_t.write(f"{label}：", font=(PANEL_FONT, 10, "normal"))
                    info_t.goto(info_box_x + PAD + 60, y)
                    info_t.color("#bbbbbb")
                    info_t.write(text, font=(PANEL_FONT, 10, "normal"))
                    y -= 17

                # 条目间分隔线（最后一条不画）
                if idx < len(INFO_CONTENT) - 1:
                    y -= 4
                    _draw_separator(y)
                    y -= 12

            # 底部提示
            y -= 12
            info_t.goto(info_box_x + PAD, y)
            info_t.color("#444444")
            info_t.write("再按 [i] 关闭", font=(PANEL_FONT, 10, "normal"))
            state["info_shown"] = True
        screen.update()

    # 延音队列: 按"事件"管理，每个事件 = 一个单音或一组和弦
    ringing_events = []  # [[(ch, note), ...], ...]
    MAX_EVENTS = 1       # 同时只保留1个事件发声
    bass_note = [None]

    # 空格键暂停/继续，暂停时 q/ESC 退出
    state = {"paused": paused, "quit": False, "info_shown": False}

    def _silence_all():
        """立即关闭所有正在发声的音符"""
        if not synth:
            return
        for event in ringing_events:
            for ch, n in event:
                synth.noteoff(ch, n)
        ringing_events.clear()
        if bass_note[0] is not None:
            synth.noteoff(4, bass_note[0])
            bass_note[0] = None

    def toggle_pause():
        state["paused"] = not state["paused"]
        if state["paused"]:
            _silence_all()  # 暂停时立刻静音

    def request_quit():
        if state["paused"]:
            state["quit"] = True

    screen.listen()
    screen.onkey(toggle_pause, "space")
    screen.onkey(request_quit, "q")
    screen.onkey(request_quit, "Escape")
    screen.onkey(toggle_info, "i")

    def wait_with_pause(duration):
        """等待指定时长，期间响应暂停/继续/退出键"""
        end = time.time() + duration
        while True:
            while state["paused"] and not state["quit"]:
                screen._root.update()
                time.sleep(0.01)
            if state["quit"] or time.time() >= end:
                break
            screen._root.update()
            time.sleep(0.01)

    prime_index = 0
    prev_prime = None
    twin_count = 0
    cousin_count = 0
    sexy_count = 0
    sg_count = 0
    palindrome_count = 0
    max_gap = 0

    # 从 start_num 开始绘制连续的 total_numbers 个数字
    # start_num 作为新的原点(0,0)，后续数字按相对索引排列
    for i in range(total_numbers):
        num = start_num + i

        # 获取相对螺旋坐标 (i=0 -> (0,0), i=1 -> (1,0), ...)
        x, y = get_spiral_position(i)

        # 计算屏幕坐标（start_num 位于中心）
        screen_x = x * cell_size
        screen_y = y * cell_size

        if is_prime(num):
            # 质数：简洁实心圆
            color = get_color_for_prime(num, prime_index)
            gap = (num - prev_prime) if prev_prime is not None else 0

            # 检测特殊质数类型
            is_twin = prev_prime is not None and gap == 2
            is_cousin = prev_prime is not None and gap == 4
            is_sexy = prev_prime is not None and gap == 6
            is_sg = is_sophie_germain(num)
            is_palin = is_palindrome(num)

            # --- 音效 ---
            if synth:
                # 延音管理：淘汰最老的事件（整组和弦一起关闭）
                while len(ringing_events) >= MAX_EVENTS:
                    for ch, n in ringing_events.pop(0):
                        synth.noteoff(ch, n)

                # 波浪式旋律：音符沿调式上行再下行，自然流畅
                scale_len = len(note_map[0])
                walk_len = scale_len * 2 - 2  # 例: 6音调式 -> 周期10
                walk_pos = prime_index % walk_len
                note_idx = walk_pos if walk_pos < scale_len else walk_len - walk_pos
                # 每个完整波浪周期交替八度 (C4 ↔ C5)
                octave = (prime_index // walk_len) % 2
                midi_note = note_map[octave][note_idx]
                # 轻柔力度：30-42
                velocity = min(30 + gap, 42)

                event = []
                if is_twin:
                    # 孪生：钢琴柔和三和弦
                    for offset, vel_adj in [(0, 0), (4, -5), (7, -10)]:
                        v = max(velocity + vel_adj, 20)
                        synth.noteon(1, midi_note + offset, v)
                        event.append((1, midi_note + offset))
                elif is_cousin:
                    # 表兄弟：竖琴五度双音
                    for offset, vel_adj in [(0, 0), (7, -5)]:
                        v = max(velocity + vel_adj, 20)
                        synth.noteon(2, midi_note + offset, v)
                        event.append((2, midi_note + offset))
                elif is_sexy:
                    # 性感：弦乐五度双音
                    for offset, vel_adj in [(0, 0), (7, -5)]:
                        v = max(velocity + vel_adj, 20)
                        synth.noteon(3, midi_note + offset, v)
                        event.append((3, midi_note + offset))
                else:
                    # 普通质数：单音钢琴
                    synth.noteon(0, midi_note, velocity)
                    event.append((0, midi_note))
                ringing_events.append(event)

                # 弦乐铺底：每 16 个质数换一次根音
                if prime_index % 16 == 0:
                    if bass_note[0] is not None:
                        synth.noteoff(4, bass_note[0])
                    bass_note[0] = note_map[0][note_idx]
                    synth.noteon(4, bass_note[0], 15)  # 极轻弦乐

            # --- 统计 ---
            if prev_prime is not None:
                if is_twin:
                    twin_count += 1
                if is_cousin:
                    cousin_count += 1
                if is_sexy:
                    sexy_count += 1
                if gap > max_gap:
                    max_gap = gap
            if is_sg:
                sg_count += 1
            if is_palin:
                palindrome_count += 1

            prev_prime = num
            prime_index += 1

            # --- 视觉：特殊质数光环 ---
            ring_color = None
            if is_twin:
                ring_color = "#ffd700"  # 金色
            elif is_cousin:
                ring_color = "#00e5ff"  # 青色
            elif is_sexy:
                ring_color = "#ff69b4"  # 粉色

            if ring_color:
                t.penup()
                t.goto(screen_x, screen_y - circle_radius - 2)
                t.pendown()
                t.pensize(2)
                t.color(ring_color)
                t.circle(circle_radius + 2)
                t.pensize(1)

            # 画实心圆
            t.penup()
            t.goto(screen_x, screen_y - circle_radius)
            t.pendown()
            t.color(color, color)
            t.begin_fill()
            t.circle(circle_radius)
            t.end_fill()

            # 数字文字
            text_color = get_contrast_text_color(color)
            t.penup()
            t.goto(screen_x, screen_y - font_size * 0.7)
            t.color(text_color)
            t.write(str(num), align="center", font=("Arial", font_size, "bold"))

            # Sophie Germain / 回文标记（右上角小符号）
            if is_sg or is_palin:
                marker = ""
                if is_sg:
                    marker += "\u25c6"
                if is_palin:
                    marker += "\u2605"
                t.goto(screen_x + circle_radius, screen_y + circle_radius * 0.5)
                t.color("#ffffff")
                t.write(marker, font=("Arial", font_size - 2, "bold"))

        else:
            # --- 非质数：极淡圆环 ---
            t.penup()
            t.goto(screen_x, screen_y - circle_radius)
            t.pendown()
            t.color("#2a2a2a")
            t.circle(circle_radius)

            t.penup()
            t.goto(screen_x, screen_y - (font_size - 1) * 0.7)
            t.color("#444444")
            t.write(str(num), align="center", font=("Arial", font_size - 1, "normal"))

        # 更新统计面板（每5个数字刷新一次，减少性能开销）
        if i % 5 == 0 or is_prime(num):
            stats_t.clear()
            # 背景卡片
            draw_card(stats_t, stats_x, stats_y - STATS_H, STATS_W, STATS_H)

            density = f"{prime_index / (i + 1) * 100:.1f}" if i > 0 else "0.0"
            y = stats_content_y

            # 标题
            stats_t.goto(stats_content_x, y)
            stats_t.color("#ffffff")
            stats_t.write("实时统计", font=(PANEL_FONT, 13, "bold"))
            y -= 24

            lines = [
                ("#aaaaaa", f"当前数字　{num}"),
                ("#aaaaaa", f"质数统计　{prime_index} ({density}%)"),
                ("#ffd700", f"孪生质数　{twin_count}"),
                ("#00e5ff", f"表兄弟　　{cousin_count}"),
                ("#ff69b4", f"性感质数　{sexy_count}"),
                ("#aaaaaa", f"◆ 安全　　{sg_count}"),
                ("#aaaaaa", f"★ 回文　　{palindrome_count}"),
                ("#aaaaaa", f"最大间距　{max_gap}"),
            ]
            if sound_config:
                style_c = STYLE_COLORS.get(sound_config['style'], "#666666")
                scale_c = SCALE_COLORS.get(sound_config['scale'], "#666666")
                lines.append((style_c, f"风格　　　{sound_config['style']}"))
                lines.append((scale_c, f"调式　　　{sound_config['scale']}"))
            for color, line in lines:
                stats_t.goto(stats_content_x, y)
                stats_t.color(color)
                stats_t.write(line, font=(PANEL_FONT, 11, "normal"))
                y -= 20

            # 外框图例
            y -= 8
            stats_t.goto(stats_content_x, y)
            stats_t.color("#555555")
            stats_t.write("── 外框含义 ──", font=(PANEL_FONT, 9, "normal"))
            y -= 16
            for ring_color, ring_label in [
                ("#ffd700", "○ 金色　孪生 gap=2"),
                ("#00e5ff", "○ 青色　表兄弟 gap=4"),
                ("#ff69b4", "○ 粉色　性感 gap=6"),
            ]:
                stats_t.goto(stats_content_x, y)
                stats_t.color(ring_color)
                stats_t.write(ring_label, font=(PANEL_FONT, 9, "normal"))
                y -= 14

            # 底部提示
            y -= 6
            stats_t.goto(stats_content_x, y)
            stats_t.color("#555555")
            stats_t.write("按 [i] 查看质数百科", font=(PANEL_FONT, 9, "normal"))
            y -= 16
            stats_t.goto(stats_content_x, y)
            stats_t.write("按 [Space] 暂停/继续", font=(PANEL_FONT, 9, "normal"))

        # 刷新显示并停顿0.05秒（期间可响应空格暂停）
        screen.update()
        wait_with_pause(0.05)

        if state["quit"]:
            break

    # --- 烟花尾声 ---
    def _get_divisors(n):
        """获取 n 的所有约数"""
        divs = []
        for i in range(1, int(math.sqrt(n)) + 1):
            if n % i == 0:
                divs.append(i)
                if i != n // i:
                    divs.append(n // i)
        divs.sort()
        return divs

    def _do_fireworks_finale():
        """烟花尾声：数字放大→火箭升空→约数分裂→烟花爆炸"""
        last_num = start_num + total_numbers - 1
        divisors = _get_divisors(last_num)

        _silence_all()

        fw_t = turtle.Turtle()
        fw_t.speed(0)
        fw_t.hideturtle()
        fw_t.penup()

        # 约数显示用的独立 turtle
        div_t = turtle.Turtle()
        div_t.speed(0)
        div_t.hideturtle()
        div_t.penup()

        t.clear()
        stats_t.clear()
        info_t.clear()

        scale_len = len(note_map[0]) if note_map else 6
        half_h = height // 2
        rocket_top = half_h - 80  # 火箭到达的顶部位置

        # === Phase A1: Zoom (~1s) — 数字在中心放大 ===
        for step in range(20):
            if state["quit"]:
                break
            fw_t.clear()
            fsize = 12 + int(step * 4)  # 12pt → ~92pt
            hue = (step * 0.04) % 1.0
            r, g, b = colorsys.hls_to_rgb(hue, 0.7, 1.0)
            glow = '#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255))
            fw_t.goto(0, -fsize * 0.4)
            fw_t.color(glow)
            fw_t.write(str(last_num), align="center", font=("Arial", fsize, "bold"))

            # 蓄力音：低音弦乐渐强 + 钢琴低音震音
            if synth and note_map:
                if step == 0:
                    # 低沉弦乐铺底（蓄力感）
                    synth.noteon(3, note_map[0][0] - 12, 25)
                    synth.noteon(4, note_map[0][0] - 24, 20)
                if step % 3 == 0:
                    # 钢琴低音震音，渐强
                    idx = (step // 3) % scale_len
                    vel = min(20 + step * 2, 55)
                    synth.noteon(0, note_map[0][idx], vel)
                    if step >= 3:
                        prev_idx = ((step // 3) - 1) % scale_len
                        synth.noteoff(0, note_map[0][prev_idx])

            screen.update()
            time.sleep(0.05)

        if state["quit"]:
            fw_t.clear()
            if synth:
                _silence_all()
                synth.delete()
            return

        # === Phase A2: Rocket (~1.5s) — 数字向上飞升 ===
        rocket_fsize = 92
        rocket_y = 0.0
        rocket_vy = 2.0  # 初速度，逐帧加速

        for step in range(40):
            if state["quit"]:
                break
            fw_t.clear()

            # 加速上升
            rocket_vy += 0.6
            rocket_y += rocket_vy
            if rocket_y > rocket_top:
                rocket_y = rocket_top

            # 火箭尾焰：在数字下方画几个渐小渐暗的圆点
            trail_colors = ["#ff6600", "#ff3300", "#ff0000", "#cc0000", "#880000"]
            for ti, tc in enumerate(trail_colors):
                trail_y = rocket_y - rocket_fsize * 0.5 - (ti + 1) * 18
                trail_sz = max(2, 14 - ti * 2) + random.randint(-2, 2)
                fw_t.goto(random.uniform(-8, 8), trail_y)
                fw_t.dot(max(1, trail_sz), tc)

            # 数字本体（发光色渐变为白色）
            bright = min(1.0, 0.6 + step * 0.01)
            hue = (0.08 + step * 0.005) % 1.0
            r, g, b = colorsys.hls_to_rgb(hue, bright, 1.0)
            glow = '#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255))
            fw_t.goto(0, rocket_y - rocket_fsize * 0.4)
            fw_t.color(glow)
            fw_t.write(str(last_num), align="center", font=("Arial", rocket_fsize, "bold"))

            # 火箭升空音：快速上行滑音 + 竖琴颤音 + 弦乐渐强
            if synth and note_map:
                if step == 0:
                    # 关闭蓄力音
                    synth.noteoff(3, note_map[0][0] - 12)
                    synth.noteoff(4, note_map[0][0] - 24)
                # 钢琴快速上行（每帧换音，模拟呼啸）
                if step % 2 == 0:
                    idx = (step // 2) % scale_len
                    octave = min(step // 10, 1)
                    vel = min(45 + step, 80)
                    synth.noteon(0, note_map[octave][idx], vel)
                    if step >= 2:
                        prev_idx = ((step // 2) - 1) % scale_len
                        prev_oct = min((step - 2) // 10, 1)
                        synth.noteoff(0, note_map[prev_oct][prev_idx])
                # 竖琴高音颤音（模拟火箭尾焰噼啪）
                if step % 3 == 0:
                    h_idx = (step // 3) % scale_len
                    h_midi = min(note_map[1][h_idx] + 12, 108)
                    synth.noteon(2, h_midi, random.randint(30, 55))
                    if step >= 3:
                        prev_h = min(note_map[1][((step // 3) - 1) % scale_len] + 12, 108)
                        synth.noteoff(2, prev_h)
                # 弦乐持续渐强（推进感）
                if step == 5:
                    synth.noteon(3, note_map[0][0], 30)
                    synth.noteon(3, note_map[0][0] + 7, 25)
                elif step == 20:
                    synth.noteon(4, note_map[1][0], 40)
                    synth.noteon(4, note_map[1][0] + 7, 35)

            screen.update()
            time.sleep(0.038)

            if rocket_y >= rocket_top:
                break

        if state["quit"]:
            fw_t.clear()
            if synth:
                _silence_all()
                synth.delete()
            return

        # === Phase A3: Split (~2s) — 约数分裂并坠落 ===
        fw_t.clear()

        # 分裂音效：先全部静音，然后一个大爆裂和弦
        if synth and note_map:
            for ch in range(5):
                for oct_i in range(2):
                    for n_idx in range(len(note_map[oct_i])):
                        synth.noteoff(ch, note_map[oct_i][n_idx])
                for extra in [-24, -12, 12, 19, 24]:
                    synth.noteoff(ch, note_map[0][0] + extra)
            root = note_map[0][0]
            # 爆裂和弦：钢琴猛击 + 竖琴碎裂 + 弦乐震撼
            synth.noteon(0, root, 80)           # 钢琴根音重击
            synth.noteon(0, root + 12, 75)      # 钢琴高八度
            synth.noteon(2, root + 16, 70)      # 竖琴高音
            synth.noteon(2, root + 19, 65)      # 竖琴更高
            synth.noteon(3, root + 7, 70)       # 弦乐五度
            synth.noteon(4, root - 12, 60)      # 低音弦乐

        # 为每个约数分配初始位置（从顶部散开）
        div_objects = []
        spread = min(600, len(divisors) * 50)
        for i, d in enumerate(divisors):
            # 均匀水平分布
            x_offset = -spread / 2 + (i / max(1, len(divisors) - 1)) * spread if len(divisors) > 1 else 0
            hue = (i * 0.618) % 1.0
            r, g, b = colorsys.hls_to_rgb(hue, 0.65, 0.9)
            c = '#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255))
            div_objects.append({
                'num': d,
                'x': x_offset,
                'y': rocket_top,
                'vx': random.uniform(-1.5, 1.5),
                'vy': random.uniform(1, 4),  # 初始微弱上抛
                'color': c,
                'fsize': max(10, min(28, 60 // max(1, len(str(d))))),
                'alive': True,
            })

        # 约数坠落动画
        ground_y = -half_h + 60
        for frame in range(70):  # ~2.3s
            if state["quit"]:
                break
            div_t.clear()
            any_alive = False
            for dobj in div_objects:
                if not dobj['alive']:
                    continue
                any_alive = True
                dobj['vy'] -= 0.35  # 重力
                dobj['x'] += dobj['vx']
                dobj['y'] += dobj['vy']

                # 落到底部后停止
                if dobj['y'] < ground_y:
                    dobj['y'] = ground_y
                    dobj['vy'] = 0
                    dobj['vx'] = 0

                div_t.goto(dobj['x'], dobj['y'])
                div_t.color(dobj['color'])
                div_t.write(str(dobj['num']), align="center",
                            font=("Arial", dobj['fsize'], "bold"))

            # 约数坠落音效：下行琶音 + 落地时叮咚
            if synth and note_map:
                # 持续下行钢琴音（碎片散落感）
                if frame % 4 == 0:
                    d_idx = (scale_len - 1 - (frame // 4) % scale_len)
                    d_oct = 1 if frame < 30 else 0
                    d_midi = note_map[d_oct][d_idx]
                    synth.noteon(0, d_midi, max(55 - frame // 2, 18))
                # 竖琴叮咚（模拟碎片着地）
                if frame % 6 == 0:
                    h_idx = (frame // 6) % scale_len
                    h_midi = min(note_map[1][h_idx] + 12, 108)
                    synth.noteon(2, h_midi, max(50 - frame // 2, 20))
                # 关闭分裂和弦（渐退）
                if frame == 15:
                    root = note_map[0][0]
                    for ch, offset in [(0, 0), (0, 12), (2, 16), (2, 19), (3, 7), (4, -12)]:
                        synth.noteoff(ch, root + offset)

            screen.update()
            time.sleep(0.033)
            if not any_alive:
                break

        # 短暂停顿，展示约数
        time.sleep(0.5)

        if state["quit"]:
            fw_t.clear()
            div_t.clear()
            if synth:
                _silence_all()
                synth.delete()
            return

        # 将约数和原数转为五颜六色的漂浮球体
        floaters = []
        half_w = width // 2

        def _rand_bright_color():
            """生成随机鲜艳颜色"""
            h = random.random()
            s = random.uniform(0.8, 1.0)
            l = random.uniform(0.55, 0.7)
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            return '#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255))

        # 原数（大号，居中偏上，鲜艳随机色）
        floaters.append({
            'text': str(last_num), 'x': 0.0, 'y': 80.0,
            'vx': random.uniform(-0.3, 0.3), 'vy': random.uniform(-0.2, 0.2),
            'fsize': 48,
            'color': _rand_bright_color(),
            'phase': random.uniform(0, 2 * math.pi),
            'freq': random.uniform(0.03, 0.06),
            'amp_x': random.uniform(0.4, 0.8),
            'amp_y': random.uniform(0.3, 0.6),
        })
        # 约数散布（每个都是不同的鲜艳色）
        for i, dobj in enumerate(div_objects):
            floaters.append({
                'text': str(dobj['num']),
                'x': dobj['x'],
                'y': random.uniform(-half_h * 0.4, half_h * 0.5),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-0.3, 0.3),
                'fsize': dobj['fsize'],
                'color': _rand_bright_color(),
                'phase': random.uniform(0, 2 * math.pi),
                'freq': random.uniform(0.02, 0.07),
                'amp_x': random.uniform(0.3, 0.9),
                'amp_y': random.uniform(0.3, 0.7),
            })

        # === Phase B: Fireworks — 多波次粒子爆炸 ===
        fw_t.clear()
        div_t.clear()

        # 静音过渡，为烟花腾出声道
        if synth and note_map:
            for ch in range(5):
                for oct_i in range(2):
                    for n_idx in range(len(note_map[oct_i])):
                        synth.noteoff(ch, note_map[oct_i][n_idx])
                for extra in [-24, -12, 12, 16, 19, 24]:
                    synth.noteoff(ch, note_map[0][0] + extra)

        # 9波次烟花配置，层次分明，第9波火树银花大结局
        # (发射帧, 中心x, 中心y, 粒子数, 速度范围, 尺寸范围, 色相偏移)
        wave_configs = [
            # Wave 1: 开场中心爆破（金色）
            (0,    0,   50,   70, (5, 14), (6, 16), 0.12),
            # Wave 2: 左侧红色花束
            (20, -220,  120,  55, (4, 12), (5, 14), 0.0),
            # Wave 3: 右侧蓝紫瀑布
            (35,  220,  130,  55, (4, 13), (5, 14), 0.7),
            # Wave 4: 双侧对称绿色
            (50, -160,  -30,  40, (3, 11), (4, 12), 0.33),
            (50,  160,  -30,  40, (3, 11), (4, 12), 0.33),
            # Wave 5: 高空粉色瀑布
            (65,    0,  200,  60, (5, 15), (6, 16), 0.9),
            # Wave 6: 三点同时（橙 + 青 + 紫）
            (80, -250,   60,  35, (3, 10), (4, 11), 0.08),
            (80,    0, -100,  35, (3, 10), (4, 11), 0.5),
            (80,  250,   60,  35, (3, 10), (4, 11), 0.78),
            # Wave 7: 宽幅银色瀑布
            (95, -100,  180,  50, (4, 12), (5, 14), 0.15),
            (95,  100,  180,  50, (4, 12), (5, 14), 0.15),
            # Wave 8: 四角齐放（彩虹色）
            (110, -280,  160, 40, (4, 11), (5, 13), 0.0),
            (110,  280,  160, 40, (4, 11), (5, 13), 0.25),
            (110, -280, -100, 40, (4, 11), (5, 13), 0.5),
            (110,  280, -100, 40, (4, 11), (5, 13), 0.75),
            # Wave 9: 火树银花大结局！！！ 全屏多点超大爆炸
            (130,    0,    0, 120, (8, 22), (10, 24), 0.0),
            (130, -200,  100,  80, (6, 18), (8, 20), 0.15),
            (130,  200,  100,  80, (6, 18), (8, 20), 0.3),
            (130, -150, -80,   80, (6, 18), (8, 20), 0.5),
            (130,  150, -80,   80, (6, 18), (8, 20), 0.65),
            (130,    0,  200,  80, (6, 18), (8, 20), 0.85),
            (133, -300,    0,  60, (5, 16), (7, 18), 0.1),
            (133,  300,    0,  60, (5, 16), (7, 18), 0.4),
            (133,    0, -160,  60, (5, 16), (7, 18), 0.7),
            (136, -100,  250,  50, (5, 15), (6, 16), 0.2),
            (136,  100,  250,  50, (5, 15), (6, 16), 0.55),
            (136, -100, -200,  50, (5, 15), (6, 16), 0.9),
            (136,  100, -200,  50, (5, 15), (6, 16), 0.45),
        ]

        # 为每个波次预生成爆炸和弦（不同音高，模拟远近不同的烟花）
        wave_chords = []
        if note_map:
            for i, wc in enumerate(wave_configs):
                w_root_idx = (i * 2) % scale_len
                w_oct = i % 2
                w_root = note_map[w_oct][w_root_idx]
                wave_chords.append(w_root)
        # 第一波次立刻起爆
        if synth and note_map and wave_chords:
            root = wave_chords[0]
            synth.noteon(0, root, 80)
            synth.noteon(0, root + 12, 70)
            synth.noteon(3, root + 7, 75)
            synth.noteon(2, root + 4, 65)

        # 预生成所有波次的粒子
        particles = []
        for spawn_frame, cx, cy, count, (spd_lo, spd_hi), (sz_lo, sz_hi), hue_off in wave_configs:
            for _ in range(count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(spd_lo, spd_hi)
                hue = (hue_off + random.uniform(-0.12, 0.12)) % 1.0
                r, g, b = colorsys.hls_to_rgb(hue, 0.65, random.uniform(0.8, 1.0))
                c = '#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255))
                particles.append({
                    'x': float(cx), 'y': float(cy),
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'color': c,
                    'size': random.uniform(sz_lo, sz_hi),
                    'spawn': spawn_frame,
                    'active': False,
                })

        sparkle_step = 0
        for frame in range(200):  # ~6.6s at 33ms/frame (9 waves)
            if state["quit"]:
                break
            fw_t.clear()
            div_t.clear()

            # 激活本帧该出现的粒子
            for p in particles:
                if not p['active'] and frame >= p['spawn']:
                    p['active'] = True

            alive = False
            for p in particles:
                if not p['active'] or p['size'] < 1:
                    continue
                alive = True
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['vy'] -= 0.12  # 轻重力，让粒子飞更远
                p['vx'] *= 0.995  # 微弱空气阻力
                p['size'] -= 0.12
                fw_t.goto(p['x'], p['y'])
                fw_t.dot(max(1, int(p['size'])), p['color'])

            # 漂浮的数字（原数 + 约数）
            bound_x = half_w - 80
            bound_y = half_h - 60
            for fl in floaters:
                # 正弦漂浮 + 缓慢漂移
                fl['x'] += fl['vx'] + math.sin(frame * fl['freq'] + fl['phase']) * fl['amp_x']
                fl['y'] += fl['vy'] + math.cos(frame * fl['freq'] * 0.7 + fl['phase']) * fl['amp_y']
                # 柔性边界反弹
                if fl['x'] > bound_x:
                    fl['vx'] = -abs(fl['vx']) - 0.1
                elif fl['x'] < -bound_x:
                    fl['vx'] = abs(fl['vx']) + 0.1
                if fl['y'] > bound_y:
                    fl['vy'] = -abs(fl['vy']) - 0.1
                elif fl['y'] < -bound_y:
                    fl['vy'] = abs(fl['vy']) + 0.1
                # 速度衰减，保持温柔
                fl['vx'] *= 0.98
                fl['vy'] *= 0.98
                div_t.goto(fl['x'], fl['y'] - fl['fsize'] * 0.4)
                div_t.color(fl['color'])
                div_t.write(fl['text'], align="center",
                            font=("Arial", fl['fsize'], "bold"))

            # === 烟花音效引擎 ===
            if synth and note_map:
                wave_frames = {w[0]: wi for wi, w in enumerate(wave_configs)}

                # --- 每波爆炸：多乐器猛击和弦 ---
                if frame in wave_frames and frame > 0:
                    wi = wave_frames[frame]
                    if wi < len(wave_chords):
                        wr = wave_chords[wi]
                        # 先关闭上一波残留
                        if wi > 0 and wi - 1 < len(wave_chords):
                            prev_r = wave_chords[wi - 1]
                            for ch, off in [(0, 0), (0, 12), (3, 7), (2, 4)]:
                                synth.noteoff(ch, prev_r + off)
                        # 爆炸和弦（每波不同音高 = 不同烟花）
                        boom_vel = random.randint(60, 80)
                        synth.noteon(0, wr, boom_vel)            # 钢琴重击
                        synth.noteon(0, wr + 12, boom_vel - 10)  # 高八度
                        synth.noteon(3, wr + 7, boom_vel - 5)    # 弦乐五度
                        synth.noteon(2, wr + 4, boom_vel - 15)   # 竖琴三度

                # --- 噼啪碎裂音：快速随机高音钢琴 ---
                if frame % 2 == 0:
                    crackle_note = random.randint(84, 102)  # C6-F#7 高音区
                    crackle_vel = random.randint(20, 45)
                    crackle_ch = random.choice([0, 1])
                    synth.noteon(crackle_ch, crackle_note, crackle_vel)
                    # 极短音，快速释放（2帧后关闭）
                    if frame >= 2:
                        synth.noteoff(crackle_ch, random.randint(84, 102))

                # --- 闪烁竖琴琶音：下行 + 上行交替 ---
                if frame % 5 == 0 and sparkle_step < 20:
                    if sparkle_step % 2 == 0:
                        s_idx = (scale_len - 1 - (sparkle_step // 2) % scale_len)
                    else:
                        s_idx = (sparkle_step // 2) % scale_len
                    s_oct = 1 if sparkle_step < 10 else 0
                    s_midi = min(note_map[s_oct][s_idx] + 12, 108)
                    s_vel = max(60 - sparkle_step * 2, 22)
                    synth.noteon(2, s_midi, s_vel)
                    sparkle_step += 1

                # --- 弦乐波浪铺底：缓慢起伏 ---
                if frame == 0:
                    synth.noteon(4, note_map[0][0] - 12, 25)
                elif frame == 50:
                    synth.noteoff(4, note_map[0][0] - 12)
                    synth.noteon(4, note_map[0][0] - 5, 30)
                elif frame == 100:
                    synth.noteoff(4, note_map[0][0] - 5)
                    synth.noteon(4, note_map[0][0], 35)
                # Wave 9 大结局：全声道齐奏加强
                elif frame == 130:
                    synth.noteoff(4, note_map[0][0])
                    synth.noteon(4, note_map[0][0] - 12, 45)
                    synth.noteon(4, note_map[0][0] - 5, 40)

            screen.update()
            time.sleep(0.033)
            if not alive and frame > 160:
                break

        # Phase C: 祝福语飘过 + 数字球缓缓漂浮
        fw_t.clear()

        if synth and note_map:
            # 全部静音
            for ch in range(5):
                for midi_n in range(21, 109):
                    synth.noteoff(ch, midi_n)

        # 祝福语 turtle
        bless_t = turtle.Turtle()
        bless_t.speed(0)
        bless_t.hideturtle()
        bless_t.penup()

        # 祝福语库（带 Emoji 装饰）
        blessings = [
            f"\u2728\U0001f389  祝福您！愿 {last_num} 为您带来无尽好运！ \U0001f389\u2728",
            f"\U0001f31f\U0001f680  数字 {last_num} 闪耀着光芒，愿它照亮您前行的路！ \U0001f680\U0001f31f",
            f"\U0001f386\U0001f3b6  在 {last_num} 的祝福下，愿您心想事成，万事如意！ \U0001f3b6\U0001f386",
            f"\U0001f340\U0001f48e  让 {last_num} 成为您的幸运数字，愿幸福与您常伴！ \U0001f48e\U0001f340",
            f"\u2b50\U0001f387  质数之美，{last_num} 之光，愿好运永远眷顾您！ \U0001f387\u2b50",
            f"\U0001f320\U0001f496  愿 {last_num} 带来满天星辰般的幸福与温暖！ \U0001f496\U0001f320",
            f"\U0001f386\U0001f38a  {last_num} 为您绽放烟花，愿新的旅程精彩纷呈！ \U0001f38a\U0001f386",
            f"\U0001f9e8\u2728  数学之美如烟花般绚烂，愿 {last_num} 为您带来惊喜！ \u2728\U0001f9e8",
        ]
        blessing = random.choice(blessings)
        bless_fsize = 32

        # 让数字球沉到下半屏慢慢漂浮
        for fl in floaters:
            fl['y'] = random.uniform(-half_h * 0.6, -half_h * 0.1)
            fl['vx'] = random.uniform(-0.3, 0.3)
            fl['vy'] = random.uniform(-0.15, 0.15)

        # 祝福语动画：缓缓从右飘到左，再缓缓返回中心定格
        bless_start_x = half_w + 500
        bless_end_x = -half_w - 500
        bless_y = 70
        total_scroll = bless_end_x - bless_start_x
        bound_x = half_w - 80
        bound_y_fl = half_h - 60

        # 横幅伴奏：缓慢音阶行走序列
        banner_melody = []
        if note_map:
            for oct in range(2):
                for idx in range(len(note_map[oct])):
                    banner_melody.append(note_map[oct][idx])
            for oct in range(1, -1, -1):
                for idx in range(len(note_map[oct]) - 1, -1, -1):
                    banner_melody.append(note_map[oct][idx])

        # 横幅周围漂浮的装饰星星粒子
        banner_stars = []
        for _ in range(20):
            banner_stars.append({
                'ox': random.uniform(-320, 320),   # 相对横幅中心的偏移
                'oy': random.uniform(-50, 70),
                'phase': random.uniform(0, 2 * math.pi),
                'freq': random.uniform(0.04, 0.1),
                'amp': random.uniform(5, 20),
                'char': random.choice(['\u2726', '\u2727', '\u2728', '\u2729', '\u2735', '\u2734', '\u00b7', '\u2022']),
                'size': random.randint(8, 16),
                'hue_off': random.random(),
            })

        # 装饰图案序列（上下交替变化）
        deco_chars_pool = [
            '\u2500\u2500 \u2726\u2727\u2726 \u2500\u2500',
            '\u2500\u2500 \u2734\u2735\u2734 \u2500\u2500',
            '\u2500\u2500 \u00b7\u2022\u00b7\u2022\u00b7 \u2500\u2500',
            '\u2500\u2500 \u2729\u2728\u2729 \u2500\u2500',
            '\u2500\u2500 \u2736\u2737\u2736 \u2500\u2500',
        ]

        def _draw_banner(bx, bf_idx):
            """绘制带动态装饰的横幅"""
            # 主文字彩虹渐变
            bh = (bf_idx * 0.005) % 1.0
            br, bg_, bb = colorsys.hls_to_rgb(bh, 0.72, 1.0)
            bcol = '#{:02x}{:02x}{:02x}'.format(int(br * 255), int(bg_ * 255), int(bb * 255))
            # 装饰色（互补色相）
            dh = (bh + 0.35) % 1.0
            dr, dg, db = colorsys.hls_to_rgb(dh, 0.6, 0.85)
            dcol = '#{:02x}{:02x}{:02x}'.format(int(dr * 255), int(dg * 255), int(db * 255))

            # 上装饰线（动态轮换图案）
            deco_idx = (bf_idx // 30) % len(deco_chars_pool)
            deco_line = deco_chars_pool[deco_idx]
            bless_t.goto(bx, bless_y + bless_fsize + 12)
            bless_t.color(dcol)
            bless_t.write(deco_line, align="center", font=(PANEL_FONT, 14, "normal"))

            # 主祝福语
            bless_t.goto(bx, bless_y)
            bless_t.color(bcol)
            bless_t.write(blessing, align="center", font=(PANEL_FONT, bless_fsize, "bold"))

            # 下装饰线（与上不同图案）
            deco_idx2 = (deco_idx + 2) % len(deco_chars_pool)
            deco_line2 = deco_chars_pool[deco_idx2]
            bless_t.goto(bx, bless_y - 18)
            bless_t.color(dcol)
            bless_t.write(deco_line2, align="center", font=(PANEL_FONT, 14, "normal"))

            # 漂浮装饰星星
            for star in banner_stars:
                sx = bx + star['ox'] + math.sin(bf_idx * star['freq'] + star['phase']) * star['amp']
                sy = bless_y + star['oy'] + math.cos(bf_idx * star['freq'] * 0.8 + star['phase']) * star['amp'] * 0.6
                # 星星闪烁：亮度随时间正弦波动
                twinkle = 0.5 + 0.5 * math.sin(bf_idx * star['freq'] * 2 + star['phase'])
                sh = (star['hue_off'] + bf_idx * 0.003) % 1.0
                sl = 0.45 + twinkle * 0.35
                sr, sg, sb = colorsys.hls_to_rgb(sh, sl, 0.9)
                scol = '#{:02x}{:02x}{:02x}'.format(int(sr * 255), int(sg * 255), int(sb * 255))
                bless_t.goto(sx, sy)
                bless_t.color(scol)
                bless_t.write(star['char'], align="center", font=("Arial", star['size'], "normal"))

        def _draw_floaters(bf_idx, amp_scale=1.0):
            """绘制漂浮的数字球"""
            for fl in floaters:
                fl['x'] += fl['vx'] + math.sin(bf_idx * fl['freq'] + fl['phase']) * fl['amp_x'] * 0.5 * amp_scale
                fl['y'] += fl['vy'] + math.cos(bf_idx * fl['freq'] * 0.7 + fl['phase']) * fl['amp_y'] * 0.3 * amp_scale
                if fl['x'] > bound_x:
                    fl['vx'] = -abs(fl['vx']) - 0.05
                elif fl['x'] < -bound_x:
                    fl['vx'] = abs(fl['vx']) + 0.05
                if fl['y'] > -half_h * 0.05:
                    fl['vy'] = -abs(fl['vy']) - 0.03
                elif fl['y'] < -bound_y_fl:
                    fl['vy'] = abs(fl['vy']) + 0.03
                fl['vx'] *= 0.99
                fl['vy'] *= 0.99
                div_t.goto(fl['x'], fl['y'] - fl['fsize'] * 0.4)
                div_t.color(fl['color'])
                div_t.write(fl['text'], align="center",
                            font=("Arial", fl['fsize'], "bold"))

        def _play_banner_music(bf_idx, melody_idx_ref):
            """横幅伴奏：钢琴缓慢旋律 + 竖琴点缀 + 弦乐铺底"""
            if not synth or not note_map or not banner_melody:
                return
            mel_len = len(banner_melody)
            # 钢琴缓慢旋律（每16帧一个音 ≈ 每1s）
            if bf_idx % 16 == 0:
                mi = melody_idx_ref[0] % mel_len
                midi = banner_melody[mi]
                synth.noteon(0, midi, 32)
                prev_mi = (melody_idx_ref[0] - 1) % mel_len
                synth.noteoff(0, banner_melody[prev_mi])
                melody_idx_ref[0] += 1
            # 竖琴点缀（每24帧 ≈ 每1.4s，错开钢琴）
            if bf_idx % 24 == 12:
                hi = melody_idx_ref[0] % mel_len
                h_midi = min(banner_melody[hi] + 12, 108)
                synth.noteon(2, h_midi, 22)
                prev_hi = (hi - 1) % mel_len
                synth.noteoff(2, min(banner_melody[prev_hi] + 12, 108))
            # 弦乐铺底：每80帧换根音（~4.8s）
            if bf_idx % 80 == 0:
                bass_root = banner_melody[melody_idx_ref[0] % mel_len] - 12
                synth.noteon(3, max(bass_root, 36), 16)
                synth.noteon(4, max(bass_root + 7, 36), 12)

        # 伴奏起始：弦乐铺底
        melody_idx = [0]
        if synth and note_map:
            root = note_map[0][0]
            synth.noteon(3, root, 20)
            synth.noteon(4, root + 7, 15)

        # Phase C1: 从右边缓缓飘到左边
        # 横幅完全可见时大幅减速，减少闪眼
        for bf in range(200):
            if state["quit"]:
                break
            bless_t.clear()
            div_t.clear()

            # 正弦缓动
            progress = bf / 199.0
            ease = 0.5 - 0.5 * math.cos(progress * math.pi)
            bx = bless_start_x + total_scroll * ease

            _draw_banner(bx, bf)
            _draw_floaters(bf)
            _play_banner_music(bf, melody_idx)

            screen.update()
            # 横幅在屏幕内时帧间隔拉长（更慢更柔和）
            if -half_w * 0.6 < bx < half_w * 0.6:
                time.sleep(0.10)
            elif -half_w < bx < half_w:
                time.sleep(0.08)
            else:
                time.sleep(0.055)

        # Phase C2: 从左边缓缓返回中心
        return_start_x = bless_end_x
        return_end_x = 0.0
        for bf in range(120):
            if state["quit"]:
                break
            bless_t.clear()
            div_t.clear()

            # 减速缓入（ease-out quartic）
            progress = bf / 119.0
            ease = 1.0 - (1.0 - progress) ** 4
            bx = return_start_x + (return_end_x - return_start_x) * ease

            _draw_banner(bx, 200 + bf)
            _draw_floaters(200 + bf, amp_scale=0.7)
            _play_banner_music(200 + bf, melody_idx)

            screen.update()
            # 越接近中心越慢
            if abs(bx) < half_w * 0.3:
                time.sleep(0.10)
            elif abs(bx) < half_w * 0.7:
                time.sleep(0.08)
            else:
                time.sleep(0.055)

        # Phase C3: 定格，祝福语居中 + 星星继续闪烁，数字球缓漂
        if synth and note_map:
            for ch in range(5):
                for midi_n in range(21, 109):
                    synth.noteoff(ch, midi_n)
            root = note_map[0][0]
            synth.noteon(0, root, 28)
            synth.noteon(2, root + 7, 20)
            synth.noteon(3, root + 4, 14)

        for bf in range(75):
            if state["quit"]:
                break
            bless_t.clear()
            div_t.clear()
            _draw_banner(0.0, 320 + bf)
            _draw_floaters(320 + bf, amp_scale=0.25)
            screen.update()
            time.sleep(0.06)

        if synth:
            synth.delete()

        screen.update()

    # --- 结尾 ---
    if fireworks and not state["quit"]:
        _do_fireworks_finale()
    elif synth and not state["quit"]:
        # 渐弱尾声
        for event in ringing_events:
            for ch, n in event:
                synth.noteoff(ch, n)
        ringing_events.clear()

        root = note_map[0][0]
        synth.noteon(0, root, 30)
        synth.noteon(2, root + 7, 22)
        synth.noteon(3, root + 4, 15)

        if bass_note[0] is not None:
            synth.noteoff(4, bass_note[0])
            bass_note[0] = None

        time.sleep(2.0)
        synth.delete()
    elif synth:
        _silence_all()
        synth.delete()

    if state["quit"]:
        turtle.bye()
    else:
        screen.update()
        screen.exitonclick()


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="绘制乌拉姆螺旋，质数用炫酷颜色高亮显示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python prime_graph.py                  # 默认中等窗口，画500个数字（从1开始）
  python prime_graph.py --size small     # 小窗口，画200个数字
  python prime_graph.py --size large     # 大窗口(宽屏)，画1200个数字
  python prime_graph.py 300              # 指定画300个数字（从1开始）
  python prime_graph.py --start 1000     # 从1000开始画500个数字
  python prime_graph.py --start 500 --count 200  # 从500开始画200个数字
  python prime_graph.py 800 --size large --start 100  # 大窗口，从100开始画800个
        """
    )
    parser.add_argument(
        "count",
        nargs="?",
        type=int,
        default=None,
        help="要绘制的数字数量 (默认: small=200, mid=500, large=1200)"
    )
    parser.add_argument(
        "--size",
        choices=["small", "mid", "large"],
        default="mid",
        help="窗口尺寸: small(800x600), mid(1400x900), large(1800x1000) (默认: mid)"
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="起始数字，默认从1开始 (例如: --start 1000)"
    )
    parser.add_argument(
        "--sound",
        action="store_true",
        default=False,
        help="开启质数音效，每个质数触发五声音阶中的一个音符"
    )
    parser.add_argument(
        "--paused",
        action="store_true",
        default=False,
        help="以暂停状态启动，按空格开始"
    )
    parser.add_argument(
        "--fireworks",
        action="store_true",
        default=False,
        help="螺旋完成后播放烟花尾声"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.count is not None and args.count <= 0:
        print("错误: 数字数量必须大于0")
        sys.exit(1)

    if args.start < 1:
        print("错误: 起始数字必须大于等于1")
        sys.exit(1)

    draw_ulam_spiral(args.count, args.size, args.start, args.sound, args.paused, args.fireworks)
