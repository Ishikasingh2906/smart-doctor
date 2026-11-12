<?php
require 'config.php';
require_role('patient');
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['cancel_id'])) {
    api('POST', '/api/patient/appointments/' . (int)$_POST['cancel_id'] . '/cancel');
    header('Location: my_appointments.php'); exit;
}
[$code, $rows] = api('GET', '/api/patient/appointments');
page_header('My appointments'); ?>
<div class="card"><h2>My appointments</h2>
<?php if ($code !== 200): ?><div class="error"><?= e($rows['error'] ?? 'Error') ?></div>
<?php elseif (!$rows): ?><p>No appointments yet. <a href="questionnaire.php">Book one</a>.</p>
<?php else: ?>
<table><tr><th>Date</th><th>Time</th><th>Doctor</th><th>Urgency</th><th>Status</th><th></th></tr>
<?php foreach ($rows as $a): ?>
  <tr><td><?= e($a['appt_date']) ?></td><td><?= e($a['appt_time']) ?></td>
      <td><?= e($a['doctor_name']) ?><br><small><?= e($a['specialization']) ?></small></td>
      <td><?= e($a['urgency']) ?></td><td><?= e($a['status']) ?></td>
      <td><?php if ($a['status'] === 'Booked'): ?>
        <form method="post" onsubmit="return confirm('Cancel this appointment?')">
          <input type="hidden" name="cancel_id" value="<?= (int)$a['id'] ?>"><button class="danger">Cancel</button></form>
      <?php endif; ?></td></tr>
<?php endforeach; ?></table>
<?php endif; ?></div>
<?php page_footer();