import base64
from io import BytesIO
import flet as ft
import qrcode


def main(page: ft.Page):
  page.title = 'QRコード生成アプリ'
  page.vertical_alignment = ft.MainAxisAlignment.CENTER
  page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
  page.theme_mode = ft.ThemeMode.LIGHT

  # 現在選択されている色を保持する変数（初期値は黒）
  current_color = '#000000'

  # QRコード生成処理
  def generate_qr(e=None):
    data = url_input.value.strip()
    if not data:
      qr_image.src = ''
      if page.controls:
        page.update()
      return

    # qrcodeの生成設定
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    # 16進数カラーコードで画像を生成
    img = qr.make_image(fill_color=current_color, back_color='white')

    buffered = BytesIO()
    img.save(buffered)
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    qr_image.src = f'data:image/png;base64,{img_base64}'
    if page.controls:
      page.update()

  # ●ボタンやパレット内の色をクリックしたとき
  def on_color_click(e):
    nonlocal current_color
    current_color = e.control.data  # 16進数コードを取得
    generate_qr()
    page.close(color_dialog)  # ★ダイアログを閉じる
    page.update()

  # パレット用の16進数カラーコード（20色）
  palette_colors = [
      '#9C27B0',
      '#673AB7',
      '#3F51B5',
      '#00BCD4',
      '#009688',
      '#4CAF50',
      '#8BC34A',
      '#CDDC39',
      '#FFEB3B',
      '#FFC107',
      '#FF9800',
      '#FF5722',
      '#E91E63',
      '#795548',
      '#9E9E9E',
      '#607D8B',
      '#1A237E',
      '#004D40',
      '#3E2723',
      '#212121',
  ]

  # カラーパレットのグリッドUIを作成
  palette_grid = ft.GridView(
      expand=1,
      runs_count=5,  # 1行に5個
      max_extent=50,
      child_aspect_ratio=1.0,
      spacing=10,
      run_spacing=10,
      controls=[
          ft.IconButton(
              icon=ft.Icons.CIRCLE,
              icon_color=color,
              data=color,
              on_click=on_color_click,
              icon_size=30,
          )
          for color in palette_colors
      ],
  )

  # カラーパレットを表示するダイアログ窓
  color_dialog = ft.AlertDialog(
      title=ft.Text('その他の色を選択'),
      content=ft.Container(content=palette_grid, width=280, height=220),
  )

  # ★重要：あらかじめoverlayに登録しておく
  page.overlay.append(color_dialog)

  # パレットを開くボタンの処理
  def open_color_picker(e):
    page.open(color_dialog)  # ★ダイアログを開く
    page.update()

  # UIコンポーネントの定義
  url_input = ft.TextField(
      label='URLや文字列を入力',
      value='https://google.com',
      width=400,
      autofocus=True,
      on_change=generate_qr,
  )

  qr_image = ft.Image(width=300, height=300, fit=ft.ImageFit.CONTAIN)

  # 横並びのカラーセレクター（●ボタン + パレットアイコン）
  color_selector = ft.Row(
      controls=[
          ft.Text('色:', weight=ft.FontWeight.BOLD),
          # 黒 ●
          ft.IconButton(
              icon=ft.Icons.CIRCLE,
              icon_color='#000000',
              data='#000000',
              on_click=on_color_click,
          ),
          # 赤 ●
          ft.IconButton(
              icon=ft.Icons.CIRCLE,
              icon_color='#FF0000',
              data='#FF0000',
              on_click=on_color_click,
          ),
          # 青 ●
          ft.IconButton(
              icon=ft.Icons.CIRCLE,
              icon_color='#0000FF',
              data='#0000FF',
              on_click=on_color_click,
          ),
          # 緑 ●
          ft.IconButton(
              icon=ft.Icons.CIRCLE,
              icon_color='#008000',
              data='#008000',
              on_click=on_color_click,
          ),
          # その他の色（カラーパレットを開くボタン）
          ft.IconButton(
              icon=ft.Icons.PALETTE,
              tooltip='その他の色を選択',
              on_click=open_color_picker,
          ),
      ],
      alignment=ft.MainAxisAlignment.CENTER,
  )

  # 画面サイズに合わせてQRコードのサイズを再計算
  def resize_qr(e):
    calculated_size = page.width * 0.4
    final_size = max(200, min(500, calculated_size))
    qr_image.width = final_size
    qr_image.height = final_size
    page.update()

  page.on_resize = resize_qr

  # 初期起動時のQRコード生成
  generate_qr()

  # 画面の配置
  page.add(
      ft.Text('QRコード ジェネレーター', size=24, weight=ft.FontWeight.BOLD),
      url_input,
      color_selector,
      ft.Container(content=qr_image, padding=20),
  )

  # 起動直後のサイズ合わせ
  resize_qr(None)

if __name__ == "__main__":
    # Webアプリとしてポート指定で起動（Renderの環境変数に対応）
    import os
    port = int(os.getenv("PORT", 8000))
    t.app(target=main, host="0.0.0.0", view=ft.AppView.WEB_BROWSER, port=port)
