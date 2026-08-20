import base64
import colorsys
import os
from io import BytesIO
import struct  # PNGバイナリを直接組み立てるための標準ライブラリ
import zlib    # PNGデータを高速圧縮するための標準ライブラリ
import flet as ft
import qrcode


# RGBのタプルを16進数カラーコード（#RRGGBB）に変換するヘルパー関数
def rgb_to_hex(r, g, b):
    return f"#{r:02X}{g:02X}{b:02X}"


# パワポ仕様の美しい連続カラーマップを「純粋なPNG画像」として爆速でバイナリ生成する関数
def generate_spectrum_png_base64(width=120, height=60):
    png_signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = struct.pack(">I", 13) + b"IHDR" + ihdr_data + struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data))

    raw_data = bytearray()
    mid_y = height / 2.0

    for y in range(height):
        raw_data.append(0)
        if y <= mid_y:
            s = y / mid_y
            v = 1.0
        else:
            s = 1.0
            v = 1.0 - ((y - mid_y) / mid_y)

        for x in range(width):
            h = x / float(width)
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            raw_data.append(int(r * 255))
            raw_data.append(int(g * 255))
            raw_data.append(int(b * 255))

    compressed_data = zlib.compress(raw_data)
    idat_chunk = struct.pack(">I", len(compressed_data)) + b"IDAT" + compressed_data + struct.pack(">I", zlib.crc32(b"IDAT" + compressed_data))
    iend_chunk = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND"))

    full_png = png_signature + ihdr_chunk + idat_chunk + iend_chunk
    return base64.b64encode(full_png).decode('utf-8')


def main(page: ft.Page):
    page.title = 'QRコード生成アプリ'
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT

    current_color = '#000000'

    # QRコード生成処理
    def generate_qr(e=None):
        data = url_input.value.strip()
        if not data:
            qr_image.src = ''
            page.update()
            return

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)

        # 【不具合の完全修正】タプル変換をやめ、16進数文字列をそのまま渡すことで確実に色が反映されます
        img = qr.make_image(
            fill_color=current_color,
            back_color='white'
        )

        buffered = BytesIO()
        img.save(buffered)
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        qr_image.src = f'data:image/png;base64,{img_base64}'
        page.update()

    # 指定された色をすべてのコンポーネントに強制同期する関数
    def sync_ui_by_hex(hex_code, update_marker=True):
        nonlocal current_color
        current_color = hex_code

        # 16進数からRGB数値を一時的にデコード（スライダー用）
        hex_clean = hex_code.lstrip('#')
        r, g, b = tuple(int(hex_clean[i:i + 2], 16) for i in (0, 2, 4))

        slider_r.value = r
        slider_g.value = g
        slider_b.value = b

        picker_preview.bgcolor = hex_code
        picker_preview.content.value = hex_code

        if update_marker:
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            spectrum_marker.left = h * float(MAP_WIDTH) - 8
            mid_y = float(MAP_HEIGHT) / 2.0
            if v < 1.0:
                spectrum_marker.top = mid_y + (1.0 - v) * mid_y - 8
            else:
                spectrum_marker.top = s * mid_y - 8

        generate_qr()

    def on_base_color_click(e):
        sync_ui_by_hex(e.control.data, update_marker=True)

    def on_slider_change(e):
        r = int(slider_r.value)
        g = int(slider_g.value)
        b = int(slider_b.value)
        hex_code = rgb_to_hex(r, g, b)
        sync_ui_by_hex(hex_code, update_marker=True)

    # --- パワポ互換連続カラーマップの構築 ---
    MAP_WIDTH = 300
    MAP_HEIGHT = 150

    spectrum_base64 = generate_spectrum_png_base64(width=120, height=60)
    color_map_image = ft.Image(
        src=f"data:image/png;base64,{spectrum_base64}",
        width=MAP_WIDTH,
        height=MAP_HEIGHT,
        fit=ft.ImageFit.FILL,
    )

    spectrum_marker = ft.Container(
        width=16,
        height=16,
        border=ft.border.all(2.5, ft.Colors.WHITE),
        border_radius=8,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=2, color=ft.Colors.BLACK54),
        left=0,
        top=0,
    )

    def on_spectrum_gesture(e: ft.DragUpdateEvent):
        x = max(0.0, min(float(MAP_WIDTH), e.local_x))
        y = max(0.0, min(float(MAP_HEIGHT), e.local_y))

        spectrum_marker.left = x - 8
        spectrum_marker.top = y - 8

        h = x / float(MAP_WIDTH)
        mid_y = float(MAP_HEIGHT) / 2.0
        if y <= mid_y:
            s = y / mid_y
            v = 1.0
        else:
            s = 1.0
            v = 1.0 - ((y - mid_y) / mid_y)

        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        hex_code = rgb_to_hex(int(r * 255), int(g * 255), int(b * 255))

        sync_ui_by_hex(hex_code, update_marker=False)

    spectrum_stack = ft.Stack(
        controls=[
            ft.Container(content=color_map_image, border_radius=4),
            spectrum_marker
        ],
        width=MAP_WIDTH,
        height=MAP_HEIGHT
    )

    spectrum_field = ft.GestureDetector(
        on_pan_update=on_spectrum_gesture,
        on_pan_start=on_spectrum_gesture,
        content=spectrum_stack
    )

    picker_preview = ft.Container(
        bgcolor=current_color,
        width=120,
        height=50,
        border_radius=6,
        border=ft.border.all(1, ft.Colors.BLACK12),
        alignment=ft.alignment.center,
        content=ft.Text(current_color, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
    )

    slider_r = ft.Slider(min=0, max=255, value=0, divisions=255, label="R: {value}", active_color=ft.Colors.RED,
                         on_change=on_slider_change)
    slider_g = ft.Slider(min=0, max=255, value=0, divisions=255, label="G: {value}", active_color=ft.Colors.GREEN,
                         on_change=on_slider_change)
    slider_b = ft.Slider(min=0, max=255, value=0, divisions=255, label="B: {value}", active_color=ft.Colors.BLUE,
                         on_change=on_slider_change)

    sliders_layout = ft.Column(
        controls=[
            ft.Row([ft.Text("R:", weight=ft.FontWeight.BOLD, width=20), slider_r], spacing=5),
            ft.Row([ft.Text("G:", weight=ft.FontWeight.BOLD, width=20), slider_g], spacing=5),
            ft.Row([ft.Text("B:", weight=ft.FontWeight.BOLD, width=20), slider_b], spacing=5),
        ],
        spacing=2,
    )

    # ダイアログ内の横並び配置
    picker_dialog_layout = ft.Row(
        controls=[
            spectrum_field,  # カラーマップ
            ft.VerticalDivider(width=10, color=ft.Colors.TRANSPARENT),
            ft.Column(
                controls=[
                    ft.Text("現在の選択色:", size=12, weight=ft.FontWeight.BOLD),
                    picker_preview,  # 色の確認エリア
                    sliders_layout,  # RGBスライダー
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # 閉じる用「✕」ボタン付きのダイアログ外枠を構築
    dialog_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("カスタム色を選択", size=16, weight=ft.FontWeight.BOLD),
                        ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda e: close_picker_dialog())
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                picker_dialog_layout
            ],
            tight=True
        ),
        width=640,
        bgcolor=ft.Colors.SURFACE,
        border_radius=12,
        padding=20,
        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK38, spread_radius=2),
    )

    # 描画ブロックを回避するため、透明な特大コンテナを敷いて最前面に重ねる自作ダイアログ
    custom_dialog_overlay = ft.Container(
        content=dialog_card,
        bgcolor="#50000000",  # 背景を半透明の黒にする（モーダル効果）
        alignment=ft.alignment.center,
        visible=False,  # 初期状態は非表示
        expand=True,
    )

    def open_picker_dialog(e):
        sync_ui_by_hex(current_color, update_marker=True)
        custom_dialog_overlay.visible = True
        page.update()

    def close_picker_dialog():
        custom_dialog_overlay.visible = False
        page.update()

    # --- メメインUIの構築 ---

    url_input = ft.TextField(
        label='URLや文字列を入力',
        value='https://google.com',
        width=400,
        autofocus=True,
        on_change=generate_qr,
    )

    qr_image = ft.Image(width=300, height=300, fit=ft.ImageFit.CONTAIN)

    # メインの色パレット行
    custom_colors_row = ft.Row(
        controls=[
            ft.Text('パレット:', weight=ft.FontWeight.BOLD),
            ft.IconButton(icon=ft.Icons.CIRCLE, icon_color='#000000', data='#000000', on_click=on_base_color_click, tooltip='黒'),
            ft.IconButton(icon=ft.Icons.CIRCLE, icon_color='#FF0000', data='#FF0000', on_click=on_base_color_click, tooltip='赤'),
            ft.IconButton(icon=ft.Icons.CIRCLE, icon_color='#0000FF', data='#0000FF', on_click=on_base_color_click, tooltip='青'),
            ft.IconButton(icon=ft.Icons.CIRCLE, icon_color='#008000', data='#008000', on_click=on_base_color_click, tooltip='緑'),
            # これを押すと確認窓＆スライダー内蔵の自作ダイアログが最前面に重なります
            ft.IconButton(
                icon=ft.Icons.COLOR_LENS,
                tooltip='カラーピッカーを開く',
                on_click=open_picker_dialog,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # アプリのメインコンテンツレイアウト
    main_content = ft.Column(
        controls=[
            ft.Text('QRコード ジェネレーター', size=24, weight=ft.FontWeight.BOLD),
            url_input,
            custom_colors_row,
            ft.Container(content=qr_image, padding=20),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15
    )

    # 画面リサイズ時にQRコードを適正サイズに調整する関数
    def resize_qr(e):
        calculated_size = page.width * 0.4
        final_size = max(200, min(500, calculated_size))
        qr_image.width = final_size
        qr_image.height = final_size
        page.update()

    page.on_resize = resize_qr

    # 初期状態のUIを黒(#000000)に同期させて起動
    sync_ui_by_hex(current_color, update_marker=True)

    # Stackを画面全体に敷き、最背面にメインアプリ、最前面に自作ダイアログを重ねる
    page.add(
        ft.Stack(
            controls=[
                ft.Container(content=main_content, alignment=ft.alignment.center, expand=True),
                custom_dialog_overlay  # 自作のポップアップダイアログレイヤー
            ],
            expand=True
        )
    )

    # 起動直後のサイズ合わせ
    resize_qr(None)


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    ft.app(target=main, host="0.0.0.0", view=ft.AppView.WEB_BROWSER, port=port)
