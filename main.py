import sys
import os
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from src.backend.database import init_db
from src.backend.game_manager import GameManager
from src.backend.account_manager import AccountManager
from src.backend.umu_runtime_manager import UMURuntimeManager
from src.backend.download_manager import DownloadManager

def main():
    # Initialize DB
    init_db()

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    game_manager = GameManager()
    account_manager = AccountManager()
    umu_manager = UMURuntimeManager()
    download_manager = DownloadManager()
    
    # Connect account changes to library refreshes
    account_manager.accounts_changed.connect(game_manager.refresh_models)
    
    engine.rootContext().setContextProperty("gameManager", game_manager)
    engine.rootContext().setContextProperty("accountManager", account_manager)
    engine.rootContext().setContextProperty("umuManager", umu_manager)
    engine.rootContext().setContextProperty("downloadManager", download_manager)

    # Load QML
    qml_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "src/ui/qml/main.qml"))
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
