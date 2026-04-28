"""V4.10.7: comprehensive destructive-command coverage regression test.

Locks every pattern added in v4.10.7 against `SECURITY.validate_command` and
`SECURITY.validate_python`. Each blocked phrase MUST return False with
a non-empty reason.

Categories covered (all added in v4.10.7 unless noted):
- Cloud CLI hard-block (gh, gcloud, gsutil, bq, az, azcopy, kubectl, helm,
  kustomize, terraform, terragrunt, pulumi, doctl, oci, ibmcloud, linode-cli,
  hcloud, heroku, vercel, netlify, wrangler, cloudflared, flyctl, railway,
  render-cli)
- Git destructive flags (reset --hard, clean -fd, checkout -- ., reflog
  expire, gc --prune)
- Package destructive (pip uninstall, conda remove, npm uninstall, apt remove,
  yum remove, dnf remove, brew uninstall)
- Storage / volume destructive (lvremove, vgremove, pvremove, zfs destroy,
  btrfs delete, mdadm --remove, cryptsetup luksClose, tar --remove-files,
  rsync/scp --delete)
- Permission destructive (chmod 000, chattr +i)
- System-file overwrite (>/etc, >/usr, etc.; echo > /etc/sudoers)
- Persistence (crontab -r, systemctl mask, pm2 delete, supervisorctl stop)
- Database CLI (psql, mysql, mongosh, redis-cli)
- Database destructive via Python (cursor.execute DROP/TRUNCATE/DELETE,
  SQLAlchemy drop_all, MongoDB dropDatabase, Redis flushall)
- Filesystem destructive via Python (os.unlink on system path, pathlib
  destructive on system path, shutil.rmtree outside tmp/home)

Pre-existing categories also re-verified:
- rm -rf classic patterns
- AWS CLI / boto3 destructive
- privilege escalation, network attacks, credential theft
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagemaker_agent as sa


# ---- Bash command tests ---------------------------------------------------

BASH_BLOCK_CASES = [
    # Cloud CLI hard-block (24 entries)
    ("gh repo delete winston/secret",                                     "GitHub CLI"),
    ("gh pr create",                                                       "GitHub CLI"),
    ("gcloud projects delete my-proj",                                     "gcloud"),
    ("gsutil rm -r gs://bucket/folder/",                                   "gsutil"),
    ("bq rm dataset.table",                                                "bq"),
    ("az group delete --name myrg",                                        "az"),
    ("azcopy remove https://account.blob.core.windows.net/container",      "azcopy"),
    ("kubectl delete ns production",                                       "kubectl"),
    ("helm uninstall my-release",                                          "helm"),
    ("kustomize build .",                                                  "kustomize"),
    ("terraform destroy -auto-approve",                                    "terraform"),
    ("terragrunt destroy",                                                 "terragrunt"),
    ("pulumi destroy --yes",                                               "pulumi"),
    ("doctl droplet delete 12345",                                         "doctl"),
    ("oci compute instance terminate --instance-id ocid1.x",               "oci"),
    ("ibmcloud sl vs cancel 12345",                                        "ibmcloud"),
    ("linode-cli linodes delete 12345",                                    "linode-cli"),
    ("hcloud server delete my-server",                                     "hcloud"),
    ("heroku apps:destroy --app my-app",                                   "heroku"),
    ("vercel rm my-project",                                               "vercel"),
    ("netlify sites:delete site_id",                                       "netlify"),
    ("wrangler delete worker-name",                                        "wrangler"),
    ("cloudflared tunnel delete name",                                     "cloudflared"),
    ("flyctl apps destroy my-app",                                         "flyctl"),
    ("railway delete",                                                     "railway"),
    ("render-cli services delete srv-xxx",                                 "render-cli"),
    # Git destructive flags
    ("git reset --hard HEAD",                                              "git reset --hard"),
    ("git clean -fd",                                                      "git clean -fd"),
    ("git clean -xfd",                                                     "git clean variant"),
    ("git checkout -- .",                                                  "git destructive checkout"),
    ("git reflog expire --expire=now --all",                               "git reflog expire"),
    ("git gc --prune=now",                                                 "git gc --prune"),
    # Package destructive
    ("pip uninstall -y numpy",                                             "pip uninstall"),
    ("pip3 uninstall pandas",                                              "pip3 uninstall"),
    ("conda remove --name myenv numpy",                                    "conda remove"),
    ("conda env remove --name myenv",                                      "conda env remove"),
    ("npm uninstall react",                                                "npm uninstall"),
    ("yarn remove lodash",                                                 "yarn remove"),
    ("apt remove curl",                                                    "apt remove"),
    ("apt-get purge nodejs",                                               "apt-get purge"),
    ("yum remove gcc",                                                     "yum remove"),
    ("dnf erase python3",                                                  "dnf erase"),
    ("brew uninstall git",                                                 "brew uninstall"),
    # Storage destructive
    ("lvremove /dev/vg0/lv0",                                              "lvremove"),
    ("vgremove vg0",                                                       "vgremove"),
    ("zfs destroy tank/dataset",                                           "zfs destroy"),
    ("btrfs subvolume delete /mnt/sub",                                    "btrfs delete"),
    ("mdadm --remove /dev/md0 /dev/sda1",                                  "mdadm remove"),
    ("cryptsetup luksClose mydisk",                                        "cryptsetup luksClose"),
    ("tar --remove-files -cf archive.tar files/",                          "tar --remove-files"),
    ("rsync -av --delete src/ dest/",                                      "rsync --delete"),
    # Permission destructive
    ("chmod 000 /home/user/file",                                          "chmod 000"),
    ("chmod -R 000 ~/work",                                                "chmod -R 000"),
    ("chattr +i /important.txt",                                           "chattr +i"),
    # System-file overwrite
    ("echo malicious > /etc/sudoers",                                      "overwrite /etc/sudoers"),
    ("cat fake > /etc/passwd",                                             "overwrite /etc/passwd"),
    # Persistence
    ("crontab -r",                                                         "crontab -r"),
    ("crontab -e",                                                         "crontab -e"),
    ("systemctl mask sshd",                                                "systemctl mask"),
    ("pm2 delete all",                                                     "pm2 delete"),
    ("supervisorctl stop myapp",                                           "supervisorctl stop"),
    # Database CLI
    ("psql -h db.host -c 'DROP TABLE users'",                              "psql CLI"),
    ("mysql -e 'TRUNCATE TABLE x'",                                        "mysql CLI"),
    ("mongosh --eval 'db.dropDatabase()'",                                 "mongosh CLI"),
    ("redis-cli FLUSHALL",                                                 "redis-cli"),
    ("sqlite3 mydb.db 'DROP TABLE x'",                                     "sqlite3 CLI"),
    # Pre-existing patterns (sanity re-check)
    ("rm -rf /",                                                           "rm -rf root"),
    ("rm -rf ~",                                                           "rm -rf home"),
    ("dd if=/dev/zero of=/dev/sda",                                        "dd raw disk"),
    ("sudo rm -rf /tmp/x",                                                 "sudo"),
    ("aws s3 rm s3://bucket/ --recursive",                                 "AWS S3 CLI"),
    ("aws ec2 terminate-instances --instance-ids i-xxx",                   "AWS EC2 CLI"),
]

BASH_ALLOW_CASES = [
    # These should pass (read-only or harmless writes within allowlist)
    "ls -la",
    "cat README.md",
    "git status",
    "git diff",
    "git log --oneline -5",
    "pwd",
    "echo hello",
    "grep -r 'foo' .",
    "wc -l file.py",
    "pytest tests/",
    "git commit -m 'message'",          # local commit allowed
    "pip install requests",              # install allowed
    "npm install",                       # install allowed
    "tar -czf out.tar.gz src/",         # benign tar (note: chmod intentionally NOT in allowlist)
]


def test_each_destructive_bash_pattern_blocks():
    failures = []
    for cmd, label in BASH_BLOCK_CASES:
        ok, reason = sa.SECURITY.validate_command(cmd)
        if ok:
            failures.append(f"  [{label}] should be BLOCKED but passed: {cmd!r}")
        elif not reason:
            failures.append(f"  [{label}] blocked but no reason: {cmd!r}")
    assert not failures, "\n".join(["Destructive commands not blocked:"] + failures)


def test_safe_bash_commands_still_pass():
    failures = []
    for cmd in BASH_ALLOW_CASES:
        ok, reason = sa.SECURITY.validate_command(cmd)
        if not ok:
            failures.append(f"  WRONGLY BLOCKED: {cmd!r}  reason={reason!r}")
    assert not failures, "\n".join(["Safe commands wrongly blocked:"] + failures)


# ---- Python destructive tests --------------------------------------------

PYTHON_BLOCK_CASES = [
    # Database destructive
    ("cursor.execute('DROP TABLE users')",                                 "cursor.execute DROP TABLE"),
    ("cursor.execute(\"TRUNCATE TABLE x\")",                              "cursor.execute TRUNCATE"),
    ("cursor.execute('DELETE FROM users')",                                "cursor.execute DELETE FROM"),
    ("session.execute('DROP DATABASE mydb')",                              "session.execute DROP DATABASE"),
    ("conn.execute('DELETE FROM critical')",                               "conn.execute DELETE FROM"),
    ("Base.metadata.drop_all(engine)",                                     "MetaData.drop_all"),
    ("session.delete(user_obj)",                                           "ORM session.delete"),
    ("db.dropDatabase()",                                                  "MongoDB dropDatabase"),
    ("collection.deleteMany({})",                                          "MongoDB deleteMany({})"),
    ("redis_client.flushall()",                                            "Redis flushall"),
    ("redis_client.flushdb()",                                             "Redis flushdb"),
    # Filesystem destructive on system paths
    ("os.unlink('/etc/passwd')",                                           "os.unlink /etc"),
    ("pathlib.Path('/etc/important').unlink()",                            "pathlib unlink /etc"),
    ("shutil.rmtree('/var/log')",                                          "shutil.rmtree /var"),
    # Pre-existing categories sanity
    ("boto3.client('iam').list_roles()",                                   "IAM blocked"),
    ("client.delete_object(Bucket='x', Key='y')",                          "S3 delete_object"),
    ("os.system('ls')",                                                    "os.system"),
    ("eval(user_input)",                                                   "eval"),
    ("subprocess.run(['ls'])",                                             "subprocess"),
    ("requests.get('http://evil')",                                        "requests blocked"),
    ("pickle.loads(b'\\x80\\x04')",                                        "pickle.loads"),
]


def test_each_destructive_python_pattern_blocks():
    failures = []
    for code, label in PYTHON_BLOCK_CASES:
        ok, reason = sa.SECURITY.validate_python(code)
        if ok:
            failures.append(f"  [{label}] should be BLOCKED but passed: {code!r}")
        elif not reason:
            failures.append(f"  [{label}] blocked but no reason: {code!r}")
    assert not failures, "\n".join(["Destructive Python patterns not blocked:"] + failures)


# ---- Approval-cannot-be-skipped tests ------------------------------------

def test_destructive_bash_never_classified_read_only():
    """V4.10.7 rule 3: SageMaker local file remove must require user check
    even if user is in auto-approve mode. The skip path is `_classify_bash_ro`.
    Any rm/delete/destructive pattern must NEVER be classified read-only."""
    destructive_should_not_be_ro = [
        "rm file.txt",
        "rm -rf folder/",
        "rm -i file.txt",                # interactive doesn't make it read-only
        "git reset --hard",
        "git clean -fd",
        "pip uninstall numpy",
        "chmod 000 file",
        "tar --remove-files -cf out.tar f/",
    ]
    for cmd in destructive_should_not_be_ro:
        is_ro = sa._classify_bash_ro(cmd)
        assert is_ro is False, (
            f"Destructive command misclassified as read-only (would skip approval): {cmd!r}"
        )


def test_high_risk_tools_never_in_always_allow_bypass():
    """V4.10.7 rule 4: bash + python_exec must always trigger approval — they
    are HIGH_RISK and excluded from `always_allow` shortcut. Verify by reading
    the dispatcher source."""
    src_path = os.path.join(os.path.dirname(__file__), "sagemaker_agent.py")
    with open(src_path, "r", encoding="utf-8") as f:
        src = f.read()
    # The dispatcher in create_chat_ui has a HIGH_RISK_TOOLS set that excludes
    # bash + python_exec from always_allow auto-approval. Verify both are in it.
    import re
    m = re.search(r'HIGH_RISK_TOOLS\s*=\s*\{([^}]+)\}', src)
    assert m, "HIGH_RISK_TOOLS set definition missing from dispatcher"
    members = m.group(1)
    for required in ("bash", "python_exec"):
        assert f'"{required}"' in members or f"'{required}'" in members, (
            f"HIGH_RISK_TOOLS missing {required!r} — would let always_allow bypass approval"
        )


if __name__ == "__main__":
    tests = [
        ("each_destructive_bash_pattern_blocks", test_each_destructive_bash_pattern_blocks),
        ("safe_bash_commands_still_pass", test_safe_bash_commands_still_pass),
        ("each_destructive_python_pattern_blocks", test_each_destructive_python_pattern_blocks),
        ("destructive_bash_never_classified_read_only", test_destructive_bash_never_classified_read_only),
        ("high_risk_tools_never_in_always_allow_bypass", test_high_risk_tools_never_in_always_allow_bypass),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            print(f"FAIL  {name}:\n{e}")
            failed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} test groups passed "
          f"(covering {len(BASH_BLOCK_CASES)} bash + {len(BASH_ALLOW_CASES)} allow + {len(PYTHON_BLOCK_CASES)} python cases)")
    sys.exit(1 if failed else 0)
