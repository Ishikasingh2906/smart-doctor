<?php
require 'config.php';
$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    [$code, $res] = api('POST', '/api/patient/login', ['email' => $_POST['email'] ?? '', 'password' => $_POST['password'] ?? '']);
    if ($code === 200) {
        $_SESSION = ['token' => $res['token'], 'role' => 'patient', 'name' => $res['name']];
        header('Location: questionnaire.php'); exit;
    }
    $error = $res['error'] ?? 'Login failed';
}
page_header('Patient login'); ?>
<div class="card"><h2>Patient login</h2>
<?php if ($error): ?><div class="error"><?= e($error) ?></div><?php endif; ?>
<form method="post">
  <label>Email</label><input type="email" name="email" required>
  <label>Password</label><input type="password" name="password" required>
  <p><button>Login</button> <a href="register.php">Create account</a></p>
</form></div>
<?php page_footer();