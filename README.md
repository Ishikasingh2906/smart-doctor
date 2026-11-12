# smart-doctor
Smart Doctor Appointment Scheduling – ML Component

## PHP frontend (talks to the Flask backend)

Run both servers at the same time:

    Terminal 1:  cd backend && python app.py          (http://127.0.0.1:5000)
    Terminal 2:  cd php && php -S localhost:8000      (open http://localhost:8000)

XAMPP instead of `php -S`: copy the php/ folder into htdocs and enable `extension=curl` in php.ini.
If Flask runs elsewhere, change API_BASE in config.php.

How login works: the PHP page logs in via the Flask API, stores the returned token in $_SESSION,
and config.php's api() helper sends it as "Authorization: Bearer <token>" on every call.

Member C: restyle these pages freely (style.css + the HTML in each file), but keep the form field names
(they come from /api/questions) and keep calling api(...) for data.