import { ensureDataDir } from './storage';
import { fullLoad, incremental } from './calendar';
import { loadEvents } from './storage';
import { runEarningsFull } from './earnings';

async function main(): Promise<void> {
  ensureDataDir();
  const cmd = process.argv[2] || 'incremental';

  switch (cmd) {
    case 'full-load':
      await fullLoad();
      break;
    case 'incremental':
      await incremental();
      break;
    case 'earnings-only': {
      const events = loadEvents();
      const updated = runEarningsFull(events);
      const { saveEvents } = await import('./storage');
      saveEvents(updated);
      console.log(`Earnings-only recalc done: ${updated.length} events.`);
      break;
    }
    default:
      console.log('Usage: node dist/index.js <full-load|incremental|earnings-only>');
      console.log('  full-load     - Fetch all calendar events and recalc all earnings.');
      console.log('  incremental   - Fetch events, merge, fill only empty earnings.');
      console.log('  earnings-only - Recalc all earnings from existing data/events.json.');
      process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
