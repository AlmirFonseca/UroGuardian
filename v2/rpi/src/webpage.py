# webpage.py
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from flask_socketio import SocketIO, emit
import matplotlib.pyplot as plt
import qrcode
import io
import base64

from src.config_manager import ConfigManager
from src.logger import Logger
from src.database import Database

class WebPage:
    """
    Classe WebPage responsável pela interface Flask da aplicação.
    Gerencia rotas de navegação, interação com banco de dados e exibição de gráficos/telas.
    """

    def __init__(self, config_manager: ConfigManager, logger: Logger, db: Database):
        self.config_manager = config_manager
        self.logger = logger
        self.db = db
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, async_mode='threading')  # Suporte multithread
        self._register_routes()
        self._register_socketio_events()

    def _register_routes(self):
        app = self.app

        @app.route('/')
        def standby():
            return render_template('standby.html')

        @app.route('/welcome')
        def welcome():
            # Dado que você deseja codificar no QR code
            project_url = "https://github.com/AlmirFonseca/UroGuardian" 
            # Gerar imagem do QR code
            img = qrcode.make(project_url)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            img_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            
            return render_template('welcome.html', qr_code=img_b64, project_url=project_url)

        @app.route('/collecting')
        def collecting():
            return render_template('collecting.html', status="Coletando dados...")

        @app.route('/processing')
        def processing():
            return render_template('processing.html', status="Processando dados de urina...")

        @app.route('/history/<int:user_id>')
        def show_history(user_id):
            # Recupera todos os dados de histórico do usuário para exibição
            history_rows = self.db.fetch_all('fetch_user_history', params=(user_id,), format="dict")
            # Busca meta-infos para o usuário (opcional)
            user_info = self.db.fetch_one(
                None,  # query_key pode ser None se usar query direta
                query="SELECT * FROM user WHERE user_id = ?",
                params=(user_id,),
                format="dict"
            )

            return render_template('history.html',
                user_id=user_id,
                user_info=user_info,
                history=history_rows
            )


        @app.route('/log')
        def logs():
            logs = self.db.fetch_all('fetch_logs')
            return render_template('logs.html', logs=logs)

        @app.route('/goodbye')
        def goodbye():
            return render_template('goodbye.html', message="Obrigado, evento registrado!")

        @app.route('/plot/spectrum/<sample_id>')
        def plot_spectrum(sample_id):
            spectrum = self.db.fetch_all('fetch_spectrum_datapoints_by_sample', params=(sample_id,), format="dict")
            fig, ax = plt.subplots()
            ax.plot(range(1, len(spectrum[0]['channels']) + 1), spectrum[0]['channels'], marker='x')
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            return send_file(buf, mimetype='image/png')
        
        @app.route('/results/', defaults={'sample_id': None})
        @app.route('/results/<int:sample_id>')
        def results(sample_id):
            
            # If no sample_id, get most recent (highest) sample_id from urine_samples
            if sample_id is None:
                latest_row = self.db.fetch_one(
                    "fetch_latest_urine_sample_id", 
                    format="tuple"
                )
                if latest_row:
                    sample_id = latest_row[0]
                else:
                    # Render a safe "no samples available" page or message
                    return render_template('results.html', urine_sample=None, spectrum_datapoints=[])


            # Pega todos os dados da amostra
            urine_sample_row = self.db.fetch_one('fetch_urine_sample_by_id', params=(sample_id,), format="dict")
            # Pega todos os spectrum datapoints para essa amostra
            spectrum_rows = self.db.fetch_all('fetch_spectrum_datapoints_by_sample', params=(sample_id,), format="dict")
            
            return render_template(
                'results.html',
                urine_sample=urine_sample_row,
                spectrum_datapoints=spectrum_rows
            )

        
    def _register_socketio_events(self):
        @self.socketio.on('connect')
        def handle_connect():
            self.logger.println("Navegador conectado via SocketIO.", "INFO")

        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.logger.println("Navegador desconectado do SocketIO.", "INFO")

    #### Main entry point for controller: use this to trocar telas!
    def update_stage(self, payload, extra_data=None):
        """Método para ser chamado pelo Controller ao mudar de etapa."""
        self.logger.println(f"WEBPAGE Atualizando etapa para: {payload} com extras: {extra_data}", "INFO")
        if extra_data:
            payload.update(extra_data)
        self.socketio.emit('stage_update', payload)
        self.logger.println(f"WEBPAGE Emitindo mudança de etapa: {payload.get("stage", None)} ({payload})", "INFO")

    def run(self, host="0.0.0.0", port=5000, debug=False):
        # self.app.run(host=host, port=port, debug=debug)
        # Troque para self.socketio.run!
        self.logger.println(f"Iniciando WebPage em http://{host}:{port} (debug={debug})", "INFO")
        self.socketio.run(self.app, host=host, port=port, debug=debug)