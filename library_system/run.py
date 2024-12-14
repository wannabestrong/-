from app import create_app

app = create_app()

if __name__ == '__main__':
    print("启动服务器...")
    app.run(debug=True) 