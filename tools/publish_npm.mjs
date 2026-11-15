#!/usr/bin/env node
/**
 * Publish whale-aside to npm, then move the market index onto the npm channel.
 *
 * Publishing is effectively irreversible: after the 72-hour unpublish window the
 * version is permanent, the name stays reserved, and mirrors (jsDelivr, unpkg,
 * npmmirror) start serving the tarball — which contains the third-party sticker
 * artwork shipped as-is under PROVENANCE.md. So this script **refuses to publish
 * unless `--yes` is passed** and otherwise only reports what would happen.
 *
 * It also refuses to touch the index until the registry actually has the version,
 * because an index entry pointing at an unpublished package is a broken listing.
 *
 * Usage:
 *   node tools/publish_npm.mjs            # safe: auth check + dry run only
 *   node tools/publish_npm.mjs --yes      # publish for real, then switch the index
 *   node tools/publish_npm.mjs --yes --otp 123456
 */
import { execFile } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';

const run = promisify(execFile);
const BASE = join(dirname(fileURLToPath(import.meta.url)), '..');
const PKG_DIR = join(BASE, 'whale-aside');
const args = process.argv.slice(2);
const GO = args.includes('--yes');
const otpIndex = args.indexOf('--otp');
const OTP = otpIndex !== -1 && typeof args[otpIndex + 1] === 'string' ? args[otpIndex + 1] : '';

const pkg = JSON.parse(await readFile(join(PKG_DIR, 'package.json'), 'utf8'));
console.log(`package : ${pkg.name}@${pkg.version}`);
console.log(`mode    : ${GO ? 'PUBLISH FOR REAL' : 'dry run (pass --yes to publish)'}`);

/* On Windows `npm` is `npm.cmd`, and Node refuses to spawn .cmd without a shell, so
 * the shell form is used. Every argument here is a fixed literal; the only variable
 * input is the OTP, which is validated to six digits before it reaches the command
 * line, so nothing user-supplied can inject into it. */
const NPM = process.platform === 'win32' ? 'npm.cmd' : 'npm';

async function npm(cmd) {
  let tail = '';
  if (cmd.startsWith('publish') && OTP !== '') {
    if (/^\d{6}$/.test(OTP) === false) throw new Error('--otp must be exactly six digits');
    tail = ` --otp ${OTP}`;
  }
  try {
    const { stdout } = await run(`${NPM} ${cmd}${tail}`, { cwd: PKG_DIR, shell: true, maxBuffer: 8 << 20 });
    return { ok: true, out: stdout };
  } catch (error) {
    return { ok: false, out: `${error.stdout ?? ''}${error.stderr ?? ''}${error.message}` };
  }
}

/* 1. auth first: publishing without it wastes a build and leaves a confusing error */
const who = await npm('whoami');
if (who.ok === false) {
  console.error('\nNOT LOGGED IN. npm never received credentials on this machine.');
  console.error('The web flow has already failed twice here, so use a token instead');
  console.error('(create one at https://www.npmjs.com/access-tokens/create, Read and');
  console.error('write, then run this in YOUR OWN terminal — never paste it into chat):');
  console.error('');
  console.error('    npm config set //registry.npmjs.org/:_authToken npm_XXXXXXXX');
  console.error('');
  console.error(who.out.split('\n').slice(0, 4).join('\n'));
  process.exit(2);
}
console.log(`logged in as: ${who.out.trim()}`);

/* 2. show what would ship: this tarball carries the as-is artwork, so look first */
const dry = await npm('publish --dry-run');
console.log(dry.ok ? '\n--- tarball ---\n' + dry.out.split('\n').filter((l) => l.includes('npm notice')).slice(2, 18).join('\n')
  : `\ndry run failed:\n${dry.out.split('\n').slice(0, 12).join('\n')}`);
if (dry.ok === false) process.exit(1);

if (GO === false) {
  console.log('\nNothing published. Re-run with --yes to go ahead.');
  process.exit(0);
}

/* 3. publish */
const pub = await npm('publish');
if (pub.ok === false) {
  console.error('\nPUBLISH FAILED:\n' + pub.out.split('\n').slice(0, 20).join('\n'));
  console.error('\nThe index was left on the git channel, so the listing still works.');
  process.exit(1);
}
console.log('\npublished.');

/* 4. confirm the registry really has it before pointing the index at it */
const url = `https://registry.npmjs.org/${pkg.name}`;
let seen = false;
for (let attempt = 1; attempt <= 12 && seen === false; attempt += 1) {
  try {
    const res = await fetch(url, { headers: { 'user-agent': 'dsh-publish-check' } });
    if (res.ok) {
      const doc = await res.json();
      if (doc.versions && doc.versions[pkg.version]) {
        seen = true;
        console.log(`registry has ${pkg.name}@${pkg.version} (attempt ${attempt})`);
      }
    }
  } catch (error) {
    /* transient; the loop retries */
  }
  if (seen === false) await new Promise((r) => setTimeout(r, 5000));
}
if (seen === false) {
  console.error(`\npublished, but the registry has not served ${pkg.version} yet.`);
  console.error('Leaving the index on the git channel. Re-check with:');
  console.error(`  node tools/verify_live_index.mjs`);
  process.exit(1);
}

/* 5. only now switch the advertised channel, and validate the result */
await run(process.execPath, [join(BASE, 'tools', 'make_market_index.mjs'), '--source', 'npm'], { cwd: BASE });
console.log(`\nindex moved to the npm channel. Next:`);
console.log('  git add -A && git commit -m "..." && git push');
console.log('  node tools/verify_live_index.mjs   # after Pages rebuilds');
