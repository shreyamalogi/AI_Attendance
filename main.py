from os import path
from flask import Flask, render_template, redirect, url_for, request, Response
from flask_bootstrap import Bootstrap
from datetime import date, datetime, timedelta
from flask_login.utils import logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, current_user
import pandas as pd
import os
from werkzeug.utils import secure_filename
from ai_vid import gen_frames_video
from ai_web_cam import gen_frames
from ai_img import gen_frames_photo


UPLOAD_FOLDER = 'ImagesBasic'
UPLOAD_VIDEO = 'Video'


ALLOWED_EXTENSIONS_IMG = {'png', 'jpg', 'jpeg'}
ALLOWED_EXTENSIONS_Vid = {'mp4', 'mkv'}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fjahnf3372873hdbabnfnajfnauy'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_Video'] = UPLOAD_VIDEO

Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DataBase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


class user(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=False,
                     unique=True)
    email = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)
    is_admin = db.Column(db.Boolean(), nullable=False)


class students(db.Model):
    __tablename__ = "Students"
    id = db.Column(db.Integer(), primary_key=True)
    roll_number = db.Column(db.String(), unique=True,
                            nullable=False)
    name = db.Column(db.String(), unique=True, nullable=False)


class sems_range(db.Model):
    __tablename__ = "Sems"
    id = db.Column(db.Integer(), primary_key=True)
    start_date = db.Column(db.PickleType(), nullable=False, unique=True)
    end_date = db.Column(db.PickleType(), nullable=False, unique=True)
    csv_link = db.Column(db.String(), nullable=False, unique=True)
    no_of_classes_per_day = db.Column(db.Integer(), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return user.query.get(user_id)


@app.route('/')
def home():
    return render_template("index.html", user=current_user)


# db.session.add(user(name="naveen", password=generate_password_hash(
#     "123456789"), email="rockingnaveen12@gmail.com", is_admin=True))
# db.session.commit()
def get_sem():
    lst = sems_range.query.all()
    if not lst:
        return 1
    i = 1
    for val in lst:
        if val.end_date.date() >= datetime.now().date():
            break
        i += 1
    return i


@app.route('/login/<int:num>', methods=["POST", "GET"])
def login(num):
    # form = userform()
    err = ''
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == "POST":
        email = request.form.get("email")
        passwrd = request.form.get('password')
        us = user.query.filter_by(email=email).first()
        if us:
            if check_password_hash(us.password, passwrd):
                login_user(us)
                return redirect(url_for('home'))
            else:
                err = "incorrect email/password"
        else:
            err = "Email not found"
    if num == 0:
        val = "Admin"
    else:
        val = "Teacher"
    return render_template("login.html", number=num, err=err, user=current_user, name=val)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@ app.route('/student', methods=["GET", "POST"])
def student():
    err = ''
    val = get_sem()
    curr = sems_range.query.filter_by(id=val).first()
    if not curr:
        redirect(url_for('start'))
    if request.method == "POST":
        roll = request.form.get("roll")
        rst = students.query.filter_by(roll_number=roll).first()
        if rst:

            filename = curr.csv_link
            data = pd.read_csv(filename, header=0)
            idx = data["roll_number"].tolist().index(roll)
            lst = data.iloc[idx]
            head = data.columns.values.tolist()
            return render_template('student_table.html', user=current_user, lst=lst, head=head)
        else:
            err = 'Student not Found'
    return render_template('student-view.html', err=err, user=current_user)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMG


@ app.route('/register-student', methods=["POST", "GET"])
def register_student():
    err = ''
    if request.method == "POST":
        name = request.form.get("name").upper()
        roll = request.form.get("rollnumber")
        tmp = students(roll_number=roll, name=name)
        if students.query.filter_by(name=name).first() or students.query.filter_by(roll_number=roll).first():
            err = 'Roll number/Name already exits'
        else:
            if 'file' not in request.files:
                err = "Field Empty"
                return render_template('student-register.html', err=err, user=current_user)

            file = request.files['file']
            if file.filename == '':
                err = 'Upload png , jpg , jpeg'
                return render_template('student-register.html', err=err, user=current_user)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            ext = file.filename.split(".")[1]
            os.rename(f'ImagesBasic/{file.filename}',
                      f'ImagesBasic/{name}.{ext}')

            db.session.add(tmp)
            db.session.commit()

            return redirect(url_for('home'))

    return render_template('student-register.html', err=err, user=current_user)


@ app.route('/register/<num>', methods=["POST", "GET"])
def register(num):
    err = ''
    val = ''
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = generate_password_hash(request.form.get("password"))
        bl = False
        generate_password_hash
        if num == '1':
            bl = True
        if user.query.filter_by(name=name).first() or user.query.filter_by(email=email).first():
            err = 'User already exits'
        else:
            tmp = user(name=name, email=email, password=password, is_admin=bl)
            db.session.add(tmp)
            db.session.commit()
            return redirect(url_for('home'))
    if num == '1':
        val = "Admin"
    else:
        val = "Teacher"
    return render_template('register_.html', err=err, user=current_user, number=num, name=val)


@ app.route('/start', methods=["GET", "POST"])
def start():
    sem = get_sem()
    err = ''
    if request.method == "POST":
        st = request.form.get("trip-start")
        ed = request.form.get("trip-end")
        classes = int(request.form.get("class"))
        st_year, st_month, st_day = st.split('-')
        ed_year, ed_month, ed_day = ed.split('-')
        start_dt = datetime(int(st_year), int(st_month), int(st_day))
        ed_dt = datetime(int(ed_year), int(ed_month), int(ed_day))

        if sem > 8:
            err = "All sems Complete"
        elif start_dt > ed_dt:
            err = 'End Date should be Greater than start date'
        else:
            try:
                csv_path = f'Attendance links/{st}{ed}.csv'
                db.session.add(sems_range(start_date=start_dt,
                                          end_date=ed_dt, csv_link=csv_path, no_of_classes_per_day=classes))
                db.session.commit()
                with open(csv_path, 'w') as file:
                    pass

                lst = []
                nms = []
                for nm in students.query.all():
                    lst.append(nm.roll_number)
                    nms.append(nm.name)
                dct = {"name": nms, "roll_number": lst}
                att = pd.DataFrame(dct)
                att.to_csv(path_or_buf=csv_path, index=False)
                att = pd.read_csv(csv_path)
                cnt = 0
                while start_dt <= ed_dt:
                    if start_dt.weekday() != 6:
                        for val in range(1, classes+1):
                            att[f"{start_dt.date()}({val})"] = ' '
                            cnt += 1

                    start_dt += timedelta(days=1)

                att["total_days"] = cnt
                att.to_csv(path_or_buf=csv_path)
                redirect(url_for('add_holi'))
            except:
                err = 'date already found'

    return render_template('sem_dates.html', err=err, sem=sem, user=current_user)


def allowed_file_vid(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_Vid


def get_csv_link():
    lst = sems_range.query.all()
    if lst:
        for val in lst:
            if val.end_date.date() >= datetime.now().date():
                return val.csv_link
    return -1


@ app.route('/Upload-image/Video', methods=["GET", "POST"])
def up_img():
    err = ''
    val = get_sem()
    curr = sems_range.query.filter_by(id=val).first()
    if not curr:
        redirect(url_for('start'))
    cls_no = ' '
    val = get_sem()
    curr = sems_range.query.filter_by(id=val).first()
    if not curr:
        redirect(url_for('start'))
    if request.method == "POST":
        cls_no = request.form.get("class")
        if 'file' not in request.files:
            err = "Field Empty"
            return render_template('up_vide.html', err=err, user=current_user, classes=curr.no_of_classes_per_day)
        file = request.files['file']
        ext = file.filename.split(".")[1]
        tr = False
        if file.filename == '':
            err = 'Invalid file'
            return render_template('up_vide.html', err=err, user=current_user, classes=curr.no_of_classes_per_day)
        for val in ALLOWED_EXTENSIONS_IMG:
            if val == ext:
                tr = True
                break
        if not tr:
            if file and allowed_file_vid(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_Video'], filename))

            csv_val = get_csv_link()
            if csv_val == -1:
                redirect("url_for('start')")
            gen_frames_video(f'Video/{file.filename}', csv_val, cls_no)
            os.remove(f'Video/{file.filename}')
        else:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_Video'], filename))
            csv_val = get_csv_link()
            if csv_val == -1:
                redirect("url_for('start')")
            gen_frames_photo(f'Video/{file.filename}', csv_val, cls_no)
            os.remove(f'Video/{file.filename}')

    return render_template('up_vide.html', err=err, user=current_user, classes=curr.no_of_classes_per_day)


@ app.route('/add_holidays', methods=["GET", "POST"])
def add_holi():

    if request.method == "POST":
        val = get_sem()
        curr = sems_range.query.filter_by(id=val).first()
        if not curr:
            redirect(url_for('start'))
        st = request.form.get("trip-start")
        ed = request.form.get("trip-end")
        st_year, st_month, st_day = st.split('-')
        ed_year, ed_month, ed_day = ed.split('-')
        start_dt = datetime(int(st_year), int(st_month), int(st_day))
        ed_dt = datetime(int(ed_year), int(ed_month), int(ed_day))

        csv_path = get_csv_link()
        att = pd.read_csv(csv_path)
        while start_dt <= ed_dt:
            if start_dt.weekday() != 6:
                for tr in range(1, curr.no_of_classes_per_day+1):
                    att[f"{start_dt.date()}({tr})"] = 'H'

            start_dt += timedelta(days=1)
        att["total_days"] -= 1
        att.to_csv(path_or_buf=csv_path)

    return render_template('holidays.html', user=current_user)


@ app.route('/Edit Attendance', methods=["GET", "POST"])
def edit_att():
    err = ''
    if request.method == "POST":
        roll = request.form.get("roll")
        class_no = request.form.get("class")
        date = request.form.get("trip-start")
        sem = request.form.get("sem")
        # check
        stu = students.query.filter_by(roll_number=roll).first()
        if stu:
            edt = sems_range.query.filter_by(id=sem).first()
            csv_path = edt.csv_link
            attendance = pd.read_csv(csv_path)
            idx = attendance["name"].tolist().index(stu.name)
            attendance[f'{date}({class_no})'][idx] = 'p'
            attendance.to_csv(path_or_buf=csv_path, index=False)
        else:
            err = 'Invalid Details'
    return render_template('edit-attendance.html', err=err, user=current_user)


@app.route('/View Attendance')
def view_att():
    val = get_sem()
    curr = sems_range.query.filter_by(id=val).first()
    if not curr:
        redirect(url_for('start'))
    filename = curr.csv_link
    data = pd.read_csv(filename, header=0)
    lst = list(data.values)
    head = data.columns.values.tolist()
    return render_template('table.html', user=current_user, lst=lst, head=head)


cls_no = 0
val = 0


@ app.route('/View_cam', methods=["GET", "POST"])
def video_cam():
    global cls_no, val
    no = get_sem()
    curr = sems_range.query.filter_by(id=no).first()
    if not curr:
        redirect(url_for('start'))
    val += 1
    if val % 2 != 0:
        return render_template('get_class.html', user=current_user, classes=curr.no_of_classes_per_day)
    if request.method == "POST":
        cls_no = request.form.get("periods")
    return render_template('video-capture.html', user=current_user)


@ app.route('/video_feed')
def video_feed():
    global cls_no
    val = get_sem()
    curr = sems_range.query.filter_by(id=val).first()
    filename = curr.csv_link
    return Response(gen_frames(csv_path=filename, class_no=cls_no), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
