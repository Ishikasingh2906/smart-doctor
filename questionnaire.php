<?php
require 'config.php';
require_role('patient');

// Questions come from the backend, so the form always matches what the ML model expects.
[$qcode, $questions] = api('GET', '/api/questions');
$error = null;

if ($qcode === 200 && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $answers = [];
    foreach ($questions as $q) { $answers[$q['id']] = $_POST[$q['id']] ?? null; }
    [$code, $res] = api('POST', '/api/patient/book', ['answers' => $answers]);
    if ($code === 201 || $code === 200) {
        $_SESSION['result'] = $res;
        header('Location: result.php'); exit;
    }
    $error = $res['error'] ?? 'Could not book';
    if ($code === 401) { session_destroy(); header('Location: login.php'); exit; }
}
page_header('Symptom questionnaire'); ?>
<div class="card"><h2>Tell us about your symptoms</h2>
<?php if ($qcode !== 200): ?><div class="error"><?= e($questions['error'] ?? 'Backend unavailable') ?></div><?php endif; ?>
<?php if ($error): ?><div class="error"><?= e($error) ?></div><?php endif; ?>
<?php if ($qcode === 200): ?>
<form method="post">
  <?php foreach ($questions as $q): ?>
  <div class="q"><label><?= e($q['text']) ?></label>
    <?php foreach ($q['options'] as $i => $opt): ?>
      <label><input type="radio" name="<?= e($q['id']) ?>" value="<?= e($opt) ?>" required
        <?= (($_POST[$q['id']] ?? '') === $opt) ? 'checked' : '' ?>> <?= e($opt) ?></label>
    <?php endforeach; ?>
  </div>
  <?php endforeach; ?>
  <p><button>Check urgency &amp; book appointment</button></p>
</form>
<?php endif; ?>
<p style="font-size:.85rem;color:#666">This is a prototype and not medical advice. In an emergency call your local emergency number.</p>
</div>
<?php page_footer();