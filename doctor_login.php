<?php
require 'config.php';
$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    [$code, $res] = api('POST', '/api/doctor/login', ['email' => $_POST['email'] ?? '', 'password' => $_POST['password'] ?? '']);
    if ($code === 200) {
        $_SESSION = ['token' => $res['token'], 'role' => 'doctor', 'name' => $res['name']];
        header('Location: doctor_dashboard.php'); exit;
    }
    $error = $res['error'] ?? 'Login failed';
}
page_header('Doctor login'); ?>
<div class="card"><h2>Doctor login</h2>
<?php if ($error): ?><div class="error"><?= e($error) ?></div><?php endif; ?>
<form method="post">
  <label>Email</label><input type="email" name="email" required placeholder="doctor1@hospital.com">
  <label>Password</label><input type="password" name="password" required>
  <p><button>Login</button></p>
</form></div>
<?php page_footer();