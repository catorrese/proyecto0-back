from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy 
import enum
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from flask_jwt_extended import (create_access_token, jwt_required, get_jwt_identity, JWTManager)

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///proyecto.db'
app.config['SECRET_KEY'] = 'secret-string'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'

db = SQLAlchemy(app)

ma = Marshmallow(app)

api = Api(app)

jwt = JWTManager(app)

#Enums
class EnumCategoria(enum.Enum):
	Conferencia=1
	Seminario=2
	Congreso=3
	Curso=4


class EnumTipo(enum.Enum):
	Presencial=1
	Virtual=2


#Base de Datos
class Usuario(db.Model):

	id = db.Column(db.Integer, primary_key=True)

	correo = db.Column(db.String(80), unique=True, nullable=False)

	contrasena = db.Column(db.String(80), nullable=False)

class Evento(db.Model):

	id = db.Column(db.Integer, primary_key=True)

	nombre = db.Column(db.String(80), nullable=False)

	categoria = db.Column(db.Enum(EnumCategoria), nullable=False)

	lugar = db.Column(db.String(100), nullable=False)

	direccion = db.Column(db.String(150), nullable=False)

	fecha_inicio = db.Column(db.String(50), nullable=False)

	fecha_fin = db.Column(db.String(50), nullable=False)

	tipo = db.Column(db.Enum(EnumTipo), nullable=False)

	usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

	usuario = db.relationship('Usuario', backref=db.backref('eventos', lazy=True))


#Schemas
class Usuario_Schema(ma.Schema):

	class Meta:

		fields = ("id", "correo", "contrasena")

class Evento_Schema(ma.Schema):

	class Meta:

		fields = ("id", "nombre", "categoria", "lugar", "direccion", "fecha_inicio",
			 "fecha_fin", "tipo", "usuario_id")

usuario_schema = Usuario_Schema()
usuarios_schema = Usuario_Schema(many = True)

evento_schema = Evento_Schema()
eventos_schema = Evento_Schema(many = True)


#Rutas
class RecursoListarUsuarios(Resource):
	def get(self):
		usuarios = Usuario.query.all()
		return usuarios_schema.dump(usuarios)

	def post(self):
		nuevo_usuario = Usuario(
			correo = request.json['correo'],
			contrasena = request.json['contrasena']
		)
		buscar = Usuario.query.filter_by(correo = nuevo_usuario.correo).first()
		if buscar:
			return {'message': 'Este correo ya se ha registrado'}
		db.session.add(nuevo_usuario)
		db.session.commit()
		token = create_access_token(identity = 	nuevo_usuario.correo)
		return {'token': token, 'id_usuario': nuevo_usuario.id}

class RecursoListarEventos(Resource):
	
	def get(self,id_usuario):
		
		eventos = Evento.query.filter_by(id = id_usuario)
		return eventos_schema.dump(eventos)

	
	def post(self, id_usuario):
		#user = get_jwt_identity()
		nuevo_evento = Evento(
			nombre = request.json['nombre'],
			categoria = request.json['categoria'],
			lugar = request.json['lugar'],
			direccion = request.json['direccion'],
			fecha_inicio = request.json['fecha_inicio'],
			fecha_fin = request.json['fecha_fin'],
			tipo = request.json['tipo'],
			usuario_id = id_usuario
		)
		db.session.add(nuevo_evento)
		db.session.commit()
		return evento_schema.dump(nuevo_evento)

class RecursoLogin(Resource):
	def post(self):
		buscar = Usuario.query.filter_by(correo = request.json['correo']).first()
		if not buscar:
			return {'message':'No existe un usuario con ese correo.'}
		if buscar.contrasena == request.json['contrasena']:
			token = create_access_token(buscar.correo)
			return {'token':token}
		else:
			return {'message':'Contrasena incorrecta.'}

class RecursoUnEvento(Resource):
	
	def put(self, id_evento):
		evento = Evento.query.get_or_404(id_evento)
		if 'nombre' in request.json:
			evento.nombre = request.json['nombre']

		db.session.commit()
		return evento_schema.dump(evento)

	
	def delete(self, id_evento):
		evento = Evento.query.get_or_404(id_evento)
		db.session.delete(evento)
		db.session.commit()
		return '', 204


api.add_resource(RecursoListarUsuarios, '/usuarios')
api.add_resource(RecursoListarEventos, '/eventos2/<int:id_usuario>')
api.add_resource(RecursoLogin, '/login')
api.add_resource(RecursoUnEvento, '/eventos/<int:id_evento>')

if __name__ == '__main__':
	app.run(debug=True)
