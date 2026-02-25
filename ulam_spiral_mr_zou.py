import math
import os
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


def draw_ulam_spiral(total_numbers=None, size="mid", start_num=1, sound=False, paused=False):
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

    # 渐弱尾声
    if synth and not state["quit"]:
        # 先关闭旋律，只留低音
        for event in ringing_events:
            for ch, n in event:
                synth.noteoff(ch, n)
        ringing_events.clear()

        # 和声渐隐：三声部同时响起，让混响自然带走声音
        root = note_map[0][0]  # 调式根音
        synth.noteon(0, root, 30)       # 钢琴 根音
        synth.noteon(2, root + 7, 22)   # 竖琴 纯五度
        synth.noteon(3, root + 4, 15)   # 弦乐 大三度

        # 关闭低音铺底，只留终止和声
        if bass_note[0] is not None:
            synth.noteoff(4, bass_note[0])
            bass_note[0] = None

        # 不主动 noteoff，等自然衰减消散
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
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.count is not None and args.count <= 0:
        print("错误: 数字数量必须大于0")
        sys.exit(1)

    if args.start < 1:
        print("错误: 起始数字必须大于等于1")
        sys.exit(1)

    draw_ulam_spiral(args.count, args.size, args.start, args.sound, args.paused)
