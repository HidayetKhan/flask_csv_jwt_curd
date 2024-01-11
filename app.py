from flask import Flask,request,jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import pandas as pd
import os

app=Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

jwt = JWTManager(app)




def get_file_path(filename):
    return os.path.join(app.config['UPLOAD_FOLDER'], filename)

def read_csv_file(filename):
    file_path = get_file_path(filename)
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return None

def write_csv_file(filename, df):
    file_path = get_file_path(filename)
    df.to_csv(file_path, index=False)


# user_data_file = 'users.csv'
user_data_file = 'flakcsv.csv'
if not os.path.exists(get_file_path(user_data_file)):
    initial_user_data = {'username': [], 'password': []}
    pd.DataFrame(initial_user_data).to_csv(get_file_path(user_data_file), index=False)

@app.route('/register/<filename>', methods=['POST'])
def register(filename):
    data = request.get_json()
    if data:
        username = data.get('username')
        password = data.get('password')
        # Replace this with your actual user registration logic
        users_df = read_csv_file(filename)
        if users_df is not None and username not in users_df['username'].values:
            # Append the new user to the existing user data
            new_user = pd.DataFrame({'username': [username], 'password': [password]})
            users_df = pd.concat([users_df, new_user], ignore_index=True)
            write_csv_file(user_data_file, users_df)
            return jsonify({'message': 'Registration successful'}), 200
        else:
            return jsonify({'message': 'Username already exists'}), 400
    else:
        return jsonify({'message': 'Invalid JSON data in request'}), 400



@app.route('/login/<filename>', methods=['POST'])
def login(filename):
    data = request.get_json()
    if data:
        username = data.get('username')
        password = data.get('password')
        # Replace this with your actual user authentication logic
        users_df = read_csv_file(filename)
        if users_df is not None and \
           any(users_df['username'] == username) and \
           any(users_df['password'] == password):
            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token)
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
    else:
        return jsonify({'message': 'Invalid JSON data in request'}), 400


@app.route('/upload',methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message':'no file here'}),400
    file=request.files['file']
    if file.filename == '':
        return jsonify({'message':'file not selsected'})
    if file and file.filename.endswith('.csv'):
        file_path=get_file_path(file.filename)
        file.save(file_path)
        return jsonify({'message':'file uploaded succseefully','filename':file.filename})
    return jsonify({'message':'invalid file format,upload corect csv file'}),400


@app.route('/create/<filename>', methods=['POST'])
def create_csv(filename):
    df=read_csv_file(filename)
    if df is not None:
        new_data=request.get_json()
        if new_data:
            new_df = pd.DataFrame([new_data])
            df = pd.concat([df, new_df], ignore_index=True)
            write_csv_file(filename, df)
            return jsonify({'message':'data created sucsefully'}),200
        else:
            return jsonify({'message':'invalid data forinsertion'}),400
    else:
        return jsonify({'message':'file not found'}),401
    

@app.route('/process/<filename>', methods=['GET'])
def procee_cv(filename):
    file_path=get_file_path(filename)
    if not os.path.exists(file_path):
        return jsonify({'message':'file not found'})
    try:
        df=pd.read_csv(file_path)
        data=df.to_dict(orient='records')
        return jsonify({'filename':filename,'data':data})
    except Exception as e:
        return jsonify({'message':f'error processing csv file:{str(e)}'}),500

@app.route('/update/<filename>/<int:row_index>', methods=['PUT'])
@jwt_required()
def update_csv(filename,row_index):
    df=read_csv_file(filename)
    if df is not None:
        update_data=request.get_json()
        if update_data:
            df.iloc[row_index]=update_data
            write_csv_file(filename,df)
            return jsonify({'message':'row updated sucssesfully'}),200
        else:
            return jsonify({'message':'invalid data for update'}),400
    else:
        return jsonify({'message':'file not found'}),401
    
    
@app.route('/delete/<filename>/<int:row_index>', methods=['DELETE'])
@jwt_required()
def delete_csv(filename,row_index):
    df=read_csv_file(filename)
    if df is not None:
        df=df.drop(index=row_index)
        write_csv_file(filename,df)
        return jsonify({'message':'row delete sucssefully'}),200
    else:
        return jsonify({'message':'file not found'}),400
    






if __name__=='__main__':
        app.run(debug=True)