from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from models import db, Course, Category, User, Review
from tools import CoursesFilter, ImageSaver
from sqlalchemy import desc

bp = Blueprint('courses', __name__, url_prefix='/courses')

COURSE_PARAMS = [
    'author_id', 'name', 'category_id', 'short_desc', 'full_desc'
]

def params():
    return { p: request.form.get(p) or None for p in COURSE_PARAMS }

def search_params():
    return {
        'name': request.args.get('name'),
        'category_ids': [x for x in request.args.getlist('category_ids') if x],
    }

@bp.route('/')
def index():
    courses = CoursesFilter(**search_params()).perform()
    pagination = db.paginate(courses)
    courses = pagination.items
    categories = db.session.execute(db.select(Category)).scalars()
    return render_template('courses/index.html',
                           courses=courses,
                           categories=categories,
                           pagination=pagination,
                           search_params=search_params())

@bp.route('/new')
@login_required
def new():
    course = Course()
    categories = db.session.execute(db.select(Category)).scalars()
    users = db.session.execute(db.select(User)).scalars()
    return render_template('courses/new.html',
                           categories=categories,
                           users=users,
                           course=course)

@bp.route('/create', methods=['POST'])
@login_required
def create():
    f = request.files.get('background_img')
    img = None
    course = Course()
    try:
        if f and f.filename:
            img = ImageSaver(f).save()

        image_id = img.id if img else None
        course = Course(**params(), background_image_id=image_id)
        db.session.add(course)
        db.session.commit()
    except IntegrityError as err:
        flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
        db.session.rollback()
        categories = db.session.execute(db.select(Category)).scalars()
        users = db.session.execute(db.select(User)).scalars()
        return render_template('courses/new.html',
                            categories=categories,
                            users=users,
                            course=course)

    flash(f'Курс {course.name} был успешно добавлен!', 'success')

    return redirect(url_for('courses.index'))

@bp.route('/<int:course_id>')
def show(course_id):
    course = db.get_or_404(Course, course_id)
    reviews = db.session.query(Review).filter(Review.course_id == course_id).order_by(desc(Review.created_at)).filter(Review.user_id != current_user.id).limit(5).all()
    exist = db.session.query(Review).filter(Review.user_id == current_user.id).first()
    
    return render_template('courses/show.html', course=course, reviews=reviews, exist=exist)

@bp.route('/new_review/<int:course_id>', methods=['GET', 'POST'])
@login_required
def add_review(course_id):
    course = db.session.get(Course, course_id)
    exist = db.session.query(Review).filter(Review.user_id == current_user.id).first()
    if exist:
        flash(f'Произошла ошибка при добавлении отзыва: вы уже остывили отзыв об этом курсе', 'warning')
        return redirect(url_for('courses.show', course_id=course.id))
    if not course:
        flash('Курс не найден.', 'danger')
        return redirect(url_for('index'))  # или любая другая страница
    
    if request.method == 'POST':
        text = request.form.get('text')
        rating = request.form.get('rating')
        page = request.form.get('stran')
        try:
            new_review = Review(
                text=text,
                rating=int(rating),
                course_id=course.id,
                user_id=current_user.id
            )
            db.session.add(new_review)
            course.rating_sum += int(rating)
            course.rating_num += 1
            db.session.commit()
            flash('Ваш отзыв был добавлен!', 'success')
        except Exception as e:
            db.session.rollback()  # Откат транзакции в случае ошибки
            flash(f'Произошла ошибка при добавлении отзыва: {str(e)}', 'danger')
            if page == "1":
                return redirect(url_for('courses.view_course_reviews', course_id=course.id))
            elif page == "2":
                return redirect(url_for('courses.show', course_id=course.id))
    if page == "1":
        return redirect(url_for('courses.view_course_reviews', course_id=course.id))
    elif page == "2":
        return redirect(url_for('courses.show', course_id=course.id))


@bp.route('/<int:course_id>/reviews', methods=['GET'])
def view_course_reviews(course_id):
    course = db.session.get(Course, course_id)
    page = request.args.get('page', 1, type=int)
    
    # Получаем порядок сортировки из параметров запроса
    sort_order = request.args.get('sort', 'newest')
    
    # Фильтруем отзывы по id курса
    reviews_query = db.session.query(Review.text, Review.created_at, Review.rating , User.login).join(User).filter(Review.course_id == course_id).filter(Review.user_id != current_user.id)
    
    # Применяем сортировку в зависимости от выбранного порядка
    if sort_order == 'positive':
        reviews_query = reviews_query.order_by(Review.rating.desc(), Review.created_at.desc())
    elif sort_order == 'negative':
        reviews_query = reviews_query.order_by(Review.rating.asc(), Review.created_at.desc())
    else:  # По умолчанию сортируем по новизне
        reviews_query = reviews_query.order_by(Review.created_at.desc())
    
    # Получаем отзывы для текущей страницы
    pagination = reviews_query.paginate(page=page, per_page=3)
    reviews = pagination.items
    exist = db.session.query(Review).filter(Review.user_id == current_user.id).first()
    
    return render_template('courses/all_reviews.html', course=course, reviews=reviews, pagination=pagination, sort_order=sort_order, exist=exist)
