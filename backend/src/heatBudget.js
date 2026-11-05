const { readDb, writeDb, appendTamperEvidentLog } = require('./db');

/**
 * Rules according to competition specification:
 * - Each batch has a 60-minute budget above 8°C.
 * - Track exposure and remaining budget.
 * - Exposure above 12°C counts double (2x).
 * - Below 20% (< 12 mins remaining): "At Risk".
 * - At 0%: "Discard" and keep the red LED ON until admin reset.
 *
 * @param {object} db - Optional existing db reference to prevent overwrites
 * @param {string} fridgeId - ID of fridge reporting telemetry
 * @param {number} currentTemp - Sensor temperature in °C
 * @param {number} elapsedMinutes - Duration in minutes (default 5s = 5/60 min)
 * @returns {object} Updated batches
 */
function updateHeatExposure(db, fridgeId, currentTemp, elapsedMinutes = 0.0833) {
  let dbInstance = db || readDb();
  let modified = false;

  dbInstance.batches.forEach(batch => {
    if (batch.fridgeId === fridgeId) {
      if (currentTemp > 8.0) {
        // Multiplier: 1x for 8°C-12°C, 2x for > 12°C
        const multiplier = currentTemp > 12.0 ? 2.0 : 1.0;
        const addedExposure = elapsedMinutes * multiplier;
        
        // Accumulate exposure up to total budget
        batch.exposureMinutes = Math.min(
          batch.totalBudgetMinutes, 
          Number((batch.exposureMinutes + addedExposure).toFixed(4))
        );
        modified = true;

        if (batch.exposureMinutes >= batch.totalBudgetMinutes && !batch.discarded) {
          batch.discarded = true;
          batch.status = 'Discard';
          appendTamperEvidentLog(
            'BATCH_DISCARDED',
            `Batch ${batch.id} (${batch.name}) depleted 60m budget at ${currentTemp.toFixed(1)}°C. Red LED Latch triggered.`,
            'heat_budget_guard'
          );
        }
      }

      // Compute status dynamically
      const remainingMinutes = Math.max(0, batch.totalBudgetMinutes - batch.exposureMinutes);
      const remainingPercent = (remainingMinutes / batch.totalBudgetMinutes) * 100;

      if (batch.discarded || remainingMinutes <= 0) {
        batch.status = 'Discard';
      } else if (remainingPercent < 20.0) {
        batch.status = 'At Risk';
      } else {
        batch.status = 'Safe';
      }
    }
  });

  // If db was not passed from caller, save directly
  if (!db && modified) {
    writeDb(dbInstance);
  }

  return dbInstance.batches.filter(b => b.fridgeId === fridgeId);
}

module.exports = {
  updateHeatExposure
};
