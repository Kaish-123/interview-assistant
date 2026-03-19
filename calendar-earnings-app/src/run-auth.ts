import { runAuth } from './auth';

runAuth().catch((e) => {
  console.error(e);
  process.exit(1);
});
