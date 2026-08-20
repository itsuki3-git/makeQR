import base64
import urllib.parse
import urllib.request
import flet as ft


def main(page: ft.Page):
    # ページ基本設定
    page.title = "QRコード生成アプリ"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.padding = 20

    # UIコンポーネント定義
    text_input = ft.TextField(
        label="QRコードにするテキストやURLを入力",
        width=400,
        hint_text="https://example.com",
    )

    # 最初は非表示にしておく画像コントロール
    qr_image = ft.Image(visible=False, width=250, height=250)

    # エラーメッセージ用テキスト
    status_text = ft.Text(value="", color=ft.Colors.RED_500)

    # ボタンクリック時の処理
    def generate_qr(e):
        # 未入力チェック
        if not text_input.value:
            status_text.value = "テキストを入力してください！"
            page.update()
            return

        status_text.value = ""

        try:
            # 入力されたテキストをURLエンコード
            encoded_text = urllib.parse.quote(text_input.value)
            # 無料のQRコード生成APIのURLを構築
            api_url = f"https://qrserver.com{encoded_text}"

            # APIからQRコード画像をダウンロード（メモリ上で処理）
            with urllib.request.urlopen(api_url) as response:
                img_data = response.read()

            # Fletで表示するためにBase64文字列へエンコード
            qr_image.src_base64 = base64.b64encode(img_data).decode("utf-8")
            qr_image.visible = True

        except Exception as ex:
            status_text.value = f"エラーが発生しました: {str(ex)}"
            qr_image.visible = False

        # 画面を更新して再描画
        page.update()

    # QRコード生成ボタン
    submit_btn = ft.ElevatedButton(
        text="QRコードを生成",
        icon=ft.Icons.QR_CODE,
        on_click=generate_qr
    )

    # 画面にすべてのコントロールを配置
    page.add(
        ft.Text("QR Code Generator", size=24, weight=ft.FontWeight.BOLD),
        text_input,
        submit_btn,
        status_text,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        qr_image,
    )


if __name__ == "__main__":
    # Webアプリとしてポート指定で起動（Renderの環境変数に対応）
    import os
    port = int(os.getenv("PORT", 8000))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port)
    #ft.app(target=main, host="0.0.0.0", view=ft.AppView.WEB_BROWSER, port=port)
