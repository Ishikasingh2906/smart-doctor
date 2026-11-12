<?php
require 'config.php';
require_role('doctor');

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['complete_id'])) {
    api('POST', '/api/doctor/appointments/' . (int)$_POST['complete_id'] . '/complete');
    header('Location: doctor_dashboard.php' . (!empty($_GET['date']) ? '?date=' . urlencode($_GET['date']) : '')); exit;
}
$date = $_GET['date'] ?? '';
[$code, $appts] = api('GET', '/api/doctor/appointments' . ($date ? '?date=' . urlencode($date) : ''));
[$c2, $avail]   = api('GET', '/api/doctor/availability');
$days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
$cls  = ['Very Urgent' => 'b-Very', 'Moderate' => 'b-Moderate', 'Not Urgent' => 'b-Not'];
page_header('Doctor dashboard'); ?>
<div class="card"><h2>Appointments</h2>
<form method="get"><input type="date" name="date" value="<?= e($date) ?>" style="width:auto">
  <button>Filter by date</button> <a href="doctor_dashboard.php">Show all upcoming</a></form></div>

<?php if ($code !== 200): ?><div class="error"><?= e($appts['error'] ?? 'Error') ?></div>
<?php elseif (!$appts): ?><div class="card">No booked appointments.</div>
<?php else: ?>
<table><tr><th>Date</th><th>Time</th><th>Patient</th><th>Urgency</th><th>Symptoms</th><th></th></tr>
<?php foreach ($appts as $a): ?>
  <tr><td><?= e($a['appt_date']) ?></td><td><?= e($a['appt_time']) ?></td>
      <td><?= e($a['patient_name']) ?><br><small><?= e($a['age']) ?> / <?= e($a['gender']) ?> / <?= e($a['phone']) ?></small></td>
      <td><span class="badge <?= $cls[$a['urgency']] ?? '' ?>"><?= e($a['urgency']) ?></span></td>
      <td><small><?php foreach (($a['answers'] ?? []) as $k => $v) echo e("$k: $v") . '<br>'; ?></small></td>
      <td><form method="post"><input type="hidden" name="complete_id" value="<?= (int)$a['id'] ?>"><button>Mark done</button></form></td></tr>
<?php endforeach; ?></table>
<?php endif; ?>

<?php if ($c2 === 200): ?>
<div class="card" style="margin-top:16px"><h3>My weekly availability</h3>
  <?php foreach ($avail['weekly_schedule'] as $w): ?>
    <?= $days[$w['weekday']] ?> <?= e($w['start_time']) ?>-<?= e($w['end_time']) ?> (<?= (int)$w['slot_minutes'] ?> min slots)<br>
  <?php endforeach; ?>
  <p>Free slots in the next 7 days: <b><?= count($avail['free_slots']) ?></b> &middot;
     Booked: <b><?= count($avail['booked_slots']) ?></b></p>
</div>
<?php endif; ?>
<?php page_footer();