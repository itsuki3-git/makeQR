import base64
import colorsys
import os
from io import BytesIO
import struct  # PNGバイナリを直接組み立てるための標準ライブラリ
import zlib    # PNGデータを高速圧縮するための標準ライブラリ
import flet as ft
import qrcode
# QRコードの色変えを有効にするためのカラー描画ファクトリをインポート
import qrcode.image.styledpil


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

    # 16進数カラーコード（#RRGGBB）をRGBのタプルに変換するヘルパー関数
    def hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))

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

        rgb_color = hex_to_rgb(current_color)

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

    # --- スマホに最適化した連続カラーマップの構築 ---
    MAP_WIDTH = 260
    MAP_HEIGHT = 130

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
        height=45,
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

    slider_r.width = 180
    slider_g.width = 180
    slider_b.width = 180

    sliders_layout = ft.Column(
        controls=[
            ft.Row([ft.Text("R:", weight=ft.FontWeight.BOLD, width=15), slider_r], spacing=2,
                   alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([ft.Text("G:", weight=ft.FontWeight.BOLD, width=15), slider_g], spacing=2,
                   alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([ft.Text("B:", weight=ft.FontWeight.BOLD, width=15), slider_b], spacing=2,
                   alignment=ft.MainAxisAlignment.CENTER),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Flet標準の ft.ResponsiveRow を使用してスマホ最適化
    # 画面幅（col）に応じて、スマホ（xs）なら縦に全幅（12列）、PC（md）なら横並び（6列ずつ）に自動配置
    picker_dialog_layout = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=spectrum_field,
                alignment=ft.alignment.center,
                padding=10,
                col={"xs": 12, "md": 6}
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("現在の選択色:", size=12, weight=ft.FontWeight.BOLD),
                        picker_preview,  # 色の確認エリア
                        sliders_layout,  # RGBスライダー
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5,
                ),
                alignment=ft.alignment.center,
                padding=5,
                col={"xs": 12, "md": 6}
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # 閉じる用「✕」ボタン付きのダイアログ外枠を構築
    # 【修正】max_width を正しいプロパティである width=640 に修正しました
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
        padding=15,
        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK38, spread_radius=2),
    )

    # 【修正】Container から不正な scroll 引数を削除し、代わりに Column 側で安全にスクロールできるように設定
    custom_dialog_overlay = ft.Container(
        content=ft.Column([dialog_card], scroll=ft.ScrollMode.AUTO, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
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

    # --- メインUIの構築 ---

    # 【修正】不正な max_width を削除し、width=400 に修正しました
    url_input = ft.TextField(
        label='URLや文字列を入力',
        value='https://google.com',
        width=400,
        autofocus=True,
        on_change=generate_qr,
    )

    qr_image = ft.Image(fit=ft.ImageFit.CONTAIN)

    # メインの色パレット行
    custom_colors_row = ft.Row(
        controls=[
            ft.Text('パレット:', weight=ft.FontWeight.BOLD),
            ft.IconButton(icon=ft.Icons.CIRCLE, icon_color='#000000', data='#000000', on_click=on_base_color_click, tooltip='黒'),
            ft.IconButton(icon=ft.Icons.CIRCLE, icon_color='#FF0000', data='#FF0000', on_click=on_base_color_click, tooltip='赤'),
            ft.IconButton(icon=ft.Icons.CIRCLE, icon_color='#0000FF', data='#0000FF', on_click=on_base_color_click, tooltip='青'),
            ft.IconButton(icon=ft.Icons.CIRCLE, icon_color='#008000', data='#008000', on_click=on_base_color_click, tooltip='緑'),
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
            ft.Container(content=qr_image, padding=10),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15
    )

    # 画面サイズに合わせてQRコードのサイズを再計算
    def resize_qr(e):
        calculated_size = page.width * 0.8 if page.width < 600 else page.width * 0.4
        final_size = max(180, min(450, calculated_size))
        qr_image.width = final_size
        qr_image.height = final_size
        page.update()

    page.on_resize = resize_qr

    # 初期状態のUIを黒(#000000)に同期させて起動
    sync_ui_by_hex(current_color, update_marker=True)

    # 【修正】Container から不正な scroll 引数を削除し、代わりに上位レイアウトの機能でスクロールをサポート
    page.add(
        ft.Stack(
            controls=[
                ft.Container(content=main_content, alignment=ft.alignment.center, expand=True, padding=10),
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
