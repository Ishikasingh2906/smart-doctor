<?php
// Shared setup + helpers. Every page does: require 'config.php';
session_start();

// Address of the Flask backend deployed live on Render
const API_BASE = 'https://smart-doctor-cc7a.onrender.com';

function e($s) { return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }

/**
 * Call the Flask API.
 * Returns [httpStatus, decodedJson]. Sends the logged-in user's token automatically.
 */
function api($method, $path, $body = null) {
    $ch = curl_init(API_BASE . $path);
    $headers = ['Content-Type: application/json'];
    if (!empty($_SESSION['token'])) {
        $headers[] = 'Authorization: Bearer ' . $_SESSION['token'];
    }
    curl_setopt_array($ch, [
        CURLOPT_CUSTOMREQUEST  => $method,
        CURLOPT_HTTPHEADER     => $headers,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 10,
    ]);
    if ($body !== null) {
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($body));
    }
    $raw    = curl_exec($ch);
    $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    if ($raw === false) {
        $msg = curl_error($ch);
        curl_close($ch);
        return [0, ['error' => "Cannot reach the backend ($msg). Is the live server responding?"]];
    }
    curl_close($ch);
    return [$status, json_decode($raw, true) ?? ['error' => 'Bad response from backend']];
}

function require_role($role) {
    if (($_SESSION['role'] ?? null) !== $role) {
        header('Location: ' . ($role === 'doctor' ? 'doctor_login.php' : 'login.php'));
        exit;
    }
}

function page_header($title, $extra_head = '') { ?>
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= e($title) ?> - Smart Appointment System</title>
<link rel="stylesheet" href="style.css"><?= $extra_head ?></head><body>
<nav>
  <a href="index.php"><b>Smart Appointments</b></a>
  <span>
  <?php if (($_SESSION['role'] ?? '') === 'patient'): ?>
      <a href="questionnaire.php">Book</a> <a href="my_appointments.php">My appointments</a>
  <?php elseif (($_SESSION['role'] ?? '') === 'doctor'): ?>
      <a href="doctor_dashboard.php">Dashboard</a>
  <?php endif; ?>
  <?php if (!empty($_SESSION['role'])): ?>
      <?= e($_SESSION['name']) ?> &middot; <a href="logout.php">Logout</a>
  <?php endif; ?>
  </span>
</nav><main>
<?php }

function page_footer() { echo "</main></body></html>"; }