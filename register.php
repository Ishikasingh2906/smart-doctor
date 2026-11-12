<?php
require 'config.php';
$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    [$code, $res] = api('POST', '/api/patient/register', [
        'name' => trim($_POST['name'] ?? ''), 'age' => $_POST['age'] ?? '', 'gender' => $_POST['gender'] ?? '',
        'phone' => $_POST['phone'] ?? '', 'email' => $_POST['email'] ?? '', 'password' => $_POST['password'] ?? '',
    ]);
    if ($code === 201) {
        $_SESSION = ['token' => $res['token'], 'role' => 'patient', 'name' => $res['name']];
        header('Location: questionnaire.php'); exit;
    }
    $error = $res['error'] ?? 'Registration failed';
}
page_header('Register'); ?>
<div class="card"><h2>Patient registration</h2>
<?php if ($error): ?><div class="error"><?= e($error) ?></div><?php endif; ?>
<form method="post">
  <label>Full name</label><input type="text" name="name" required value="<?= e($_POST['name'] ?? '') ?>">
  <label>Age</label><input type="number" name="age" min="0" max="120" required value="<?= e($_POST['age'] ?? '') ?>">
  <label>Gender</label>
  <select name="gender"><option>Female</option><option>Male</option><option>Other</option></select>
  <label>Phone</label><input type="text" name="phone" value="<?= e($_POST['phone'] ?? '') ?>">
  <label>Email</label><input type="email" name="email" required value="<?= e($_POST['email'] ?? '') ?>">
  <label>Password (min 6 characters)</label><input type="password" name="password" required minlength="6">
  <p><button>Register</button> <a href="login.php">Already registered?</a></p>
</form></div>
<?php page_footer();