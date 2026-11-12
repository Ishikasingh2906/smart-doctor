<?php
require 'config.php';
require_role('patient');
$r = $_SESSION['result'] ?? null;
if (!$r) { header('Location: questionnaire.php'); exit; }
$cls = ['Very Urgent' => 'b-Very', 'Moderate' => 'b-Moderate', 'Not Urgent' => 'b-Not'][$r['urgency']] ?? '';
page_header('Your result'); ?>
<?php if (!empty($r['emergency_warning'])): ?>
  <div class="alert">&#9888; <?= e($r['emergency_message']) ?></div>
<?php endif; ?>
<div class="card">
  <h2>Urgency: <span class="badge <?= $cls ?>"><?= e($r['urgency']) ?></span></h2>
  <p>Recommended department: <b><?= e($r['specialization']) ?></b></p>
  <?php if (!empty($r['appointment'])): $a = $r['appointment']; ?>
    <h3>Your appointment</h3>
    <p>Doctor: <b><?= e($a['doctor_name']) ?></b> (<?= e($a['specialization']) ?>)<br>
       Date: <b><?= e($a['day']) ?>, <?= e($a['date']) ?></b><br>
       Time: <b><?= e($a['time']) ?></b></p>
    <?php if (!empty($a['note'])): ?><p><i><?= e($a['note']) ?></i></p><?php endif; ?>
  <?php else: ?>
    <div class="error"><?= e($r['message'] ?? 'No slot available.') ?></div>
  <?php endif; ?>
  <a class="btn" href="my_appointments.php">My appointments</a>
</div>
<?php page_footer();