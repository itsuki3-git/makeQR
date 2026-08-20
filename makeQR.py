import base64
import colorsys
import os
from io import BytesIO
import struct  # PNGバイナリを直接組み立てるための標準ライブラリ
import zlib    # PNGデータを高速圧縮するための標準ライブラリ
import flet as ft
import qrcode


# 16進数カラーコード（#RRGGBB）をRGBのタプルに変換するヘルパー関数
def hex_to_rgb(hex_str):
  hex_str = hex_str.lstrip('#')
  return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))


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

  # 横軸(X)の色相Hを計算
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
  page.scroll = ft.ScrollMode.AUTO

  current_color = '#000000'

  # QRコード生成処理
  def generate_qr(e=None):
    data = url_input.value.strip()
    if not data:
      qr_image.src = ''
      if page.controls:
        page.update()
      return

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    rgb_color = hex_to_rgb(current_color)
    img = qr.make_image(fill_color=rgb_color, back_color='white')

    buffered = BytesIO()
    img.save(buffered)
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    qr_image.src = f'data:image/png;base64,{img_base64}'
    if page.controls:
      page.update()

  # パレットの色（●）をクリックしたときの通常色選択処理
  def apply_color(color_hex):
    nonlocal current_color
    current_color = color_hex
    picker_preview.bgcolor = current_color
    picker_preview.content.value = current_color
    generate_qr()
    page.update()

  def on_base_color_click(e):
    apply_color(e.control.data)

  # 【新規】カスタム色パレットを削除する関数
  def delete_custom_color(gesture_container):
    custom_colors_row.controls.remove(gesture_container)
    page.update()

  # 【新規】右クリック・長押し対応のカスタムパレットボタンを作成する関数
  def create_custom_color_button(color_hex):
    # ジェスチャーディテクターを格納する変数をあらかじめ定義（非同期参照用）
    btn_gesture = None
    
    # 内包する実際の丸ボタン
    icon_btn = ft.IconButton(
        icon=ft.Icons.CIRCLE,
        icon_color=color_hex,
        data=color_hex,
        tooltip=f"{color_hex}\n(右クリック/長押しで削除)",
    )
    
    # クリックや長押しを個別検知するコンポーネント
    btn_gesture = ft.GestureDetector(
        content=icon_btn,
        on_tap=lambda e: apply_color(color_hex),  # 普通にタップ：色を適用
        on_secondary_tap=lambda e: delete_custom_color(btn_gesture),  # 右クリック：削除
        on_long_press_start=lambda e: delete_custom_color(btn_gesture),  # 長押し：削除
    )
    return btn_gesture

  # パレットに決定した色を追加し、ダイアログを閉じる
  def add_custom_color_to_palette(e):
    # 通常のボタンではなく、ジェスチャー付きの削除可能ボタンを生成して追加
    new_color_element = create_custom_color_button(current_color)
    custom_colors_row.controls.insert(len(custom_colors_row.controls) - 1, new_color_element)
    page.close(picker_dialog)
    page.update()

  # --- パワポ互換の高品質・超高精細・超軽量カラーマップの構築 ---
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
    nonlocal current_color
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
    current_color = rgb_to_hex(int(r * 255), int(g * 255), int(b * 255))

    picker_preview.bgcolor = current_color
    picker_preview.content.value = current_color
    generate_qr()
    page.update()

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
      width=100,
      height=40,
      border_radius=4,
      alignment=ft.alignment.center,
      content=ft.Text(current_color, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
  )

  continuous_picker_layout = ft.Column(
      controls=[
          spectrum_field,
          ft.Row(
              controls=[
                  ft.Text("選択中:"),
                  picker_preview,
                  ft.ElevatedButton("パレットに登録", on_click=add_custom_color_to_palette),
              ],
              alignment=ft.MainAxisAlignment.CENTER,
              spacing=10,
          ),
      ],
      tight=True,
      horizontal_alignment=ft.CrossAxisAlignment.CENTER,
      spacing=15,
  )

  picker_dialog = ft.AlertDialog(
      title=ft.Text("カスタム色を作成"),
      content=ft.Container(content=continuous_picker_layout, width=320, height=225, padding=5),
  )
  page.overlay.append(picker_dialog)

  def open_picker_dialog(e):
    page.open(picker_dialog)
    page.update()

  # --- メインUIの構築 ---

  url_input = ft.TextField(
      label='URLや文字列を入力',
      value='https://google.com',
      width=400,
      autofocus=True,
      on_change=generate_qr,
  )

  qr_image = ft.Image(width=300, height=300, fit=ft.ImageFit.CONTAIN)

  # メインパレット（※標準の4色は削除不可、新しく作成した色のみ削除可能です）
  custom_colors_row = ft.Row(
      controls=[
          ft.Text('パレット:', weight=ft.FontWeight.BOLD),
          ft.IconButton(icon=ft.Icons.CIRCLE, icon_color='#000000', data='#000000', on_click=on_base_color_click, tooltip='黒'),
          ft.IconButton(icon=ft.Icons.CIRCLE, icon_color='#FF0000', data='#FF0000', on_click=on_base_color_click, tooltip='赤'),
          ft.IconButton(icon=ft.Icons.CIRCLE, icon_color='#0000FF', data='#0000FF', on_click=on_base_color_click, tooltip='青'),
          ft.IconButton(icon=ft.Icons.CIRCLE, icon_color='#008000', data='#008000', on_click=on_base_color_click, tooltip='緑'),
          # パレットアイコン
          ft.IconButton(
              icon=ft.Icons.COLOR_LENS,
              tooltip='連続カラーピッカーを開く',
              on_click=open_picker_dialog,
          ),
      ],
      alignment=ft.MainAxisAlignment.CENTER,
  )

  def resize_qr(e):
    calculated_size = page.width * 0.4
    final_size = max(200, min(500, calculated_size))
    qr_image.width = final_size
    qr_image.height = final_size
    page.update()

  page.on_resize = resize_qr

  generate_qr()

  page.add(
      ft.Text('QRコード ジェネレーター', size=24, weight=ft.FontWeight.BOLD),
      url_input,
      custom_colors_row,
      ft.Container(content=qr_image, padding=20),
  )

  resize_qr(None)


if __name__ == "__main__":
  port = int(os.getenv("PORT", 8000))
  ft.app(target=main, host="0.0.0.0", view=ft.AppView.WEB_BROWSER, port=port)
