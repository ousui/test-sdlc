from common import *

def main():
    snapshot_package()
    case=OUT/'worktrees-verified';case.mkdir()
    evidence=case/'git';evidence.mkdir()
    main=case/'repo-main';main.mkdir()
    def git(root,label,*args):return command(['git','-C',str(root),*args],case,label,evidence)
    git(main,'01-init','init','--initial-branch=main')
    (main/'.gitignore').write_text('.sdlc/\n')
    (main/'README.txt').write_text('Original tracked fixture baseline\n')
    git(main,'02-add','add','.gitignore','README.txt')
    git(main,'03-commit','-c','user.name=Blade','-c','user.email=blade@breaklegsquad.com','-c','core.hooksPath=/dev/null','commit','-m','chore(fixture): initialize disposable worktree acceptance baseline')
    source=Session(main,case/'source-cli');source.initialize('main-source');seed=source.seed_change('main-source')
    source_cfg=source.ok('workspace.inspect')['config']
    unique=case/'unique-target'
    git(main,'04-add-unique','worktree','add','-b','codex/unique-target',str(unique))
    (unique/'README.txt').write_text('Target-specific product bytes must remain\n')
    target=Session(unique,case/'unique-cli')
    discovered=target.ok('workspace.discover')
    assert [r['path'] for r in discovered['candidates']]==[str(main.resolve())],discovered
    assert not (unique/'.sdlc').exists()
    save(case/'unique-selection.json',{'basis':'Authorized disposable fixture; unique discovered source selected according to sdlc-init default-copy rule','discovery':discovered,'selected':str(main.resolve())})
    clone=source.ok('workspace.clone',{'target':str(unique)})
    unique_cfg=target.ok('workspace.inspect')['config']
    assert unique_cfg['workspace_id']!=source_cfg['workspace_id']
    assert unique_cfg['store_id']!=source_cfg['store_id']
    assert unique_cfg['source_store_id']==source_cfg['store_id']
    assert unique_cfg['project_id']==source_cfg['project_id']
    assert not clone['source_authorizations_active']
    assert (unique/'README.txt').read_text()=='Target-specific product bytes must remain\n'
    copied=target.ok('change.get',change_id=seed['change_id'])
    assert copied['content']['revision']['title']=='main-source',copied
    secondary=case/'secondary-source'
    git(main,'05-add-secondary','worktree','add','-b','codex/secondary-source',str(secondary))
    other=Session(secondary,case/'secondary-cli');other.initialize('secondary-source');secondary_seed=other.seed_change('secondary-source')
    secondary_cfg=other.ok('workspace.inspect')['config']
    multiple=case/'multiple-target'
    git(main,'06-add-multiple','worktree','add','-b','codex/multiple-target',str(multiple))
    many=Session(multiple,case/'multiple-cli')
    before={str(p.relative_to(multiple)):hashlib.sha256(p.read_bytes()).hexdigest() for p in multiple.rglob('*') if p.is_file()}
    discovery=many.ok('workspace.discover')
    after={str(p.relative_to(multiple)):hashlib.sha256(p.read_bytes()).hexdigest() for p in multiple.rglob('*') if p.is_file()}
    assert before==after and not (multiple/'.sdlc').exists()
    assert {r['path'] for r in discovery['candidates']}=={str(main.resolve()),str(unique.resolve()),str(secondary.resolve())},discovery
    save(case/'multiple-selection.json',{'basis':'Explicit deterministic fixture selection: secondary-source. This is an Agent decision under local fixture authorization, not a fabricated user response or Runtime automatic choice.','discovery':discovery,'selected':str(secondary.resolve()),'discovery_read_only':True})
    clone2=other.ok('workspace.clone',{'target':str(multiple)})
    many_cfg=many.ok('workspace.inspect')['config']
    assert many_cfg['project_id']==secondary_cfg['project_id']!=source_cfg['project_id']
    assert many_cfg['source_store_id']==secondary_cfg['store_id']
    assert many_cfg['workspace_id']!=secondary_cfg['workspace_id']
    assert not clone2['source_authorizations_active']
    selected_change=many.ok('change.get',change_id=secondary_seed['change_id'])
    assert selected_change['content']['revision']['title']=='secondary-source',selected_change
    rejected=many.send('change.get',change_id=seed['change_id'])
    assert rejected['errors'][0]['code']=='CHANGE_SCOPE',rejected
    registry=git(main,'07-registry','worktree','list','--porcelain')
    save(case/'summary.json',{'unique_source_passed':True,'multiple_explicit_selection_passed':True,'source_config':source_cfg,'unique_config':unique_cfg,'secondary_config':secondary_cfg,'multiple_config':many_cfg,'source_product_not_copied':True,'multiple_discovery_read_only':True,'source_authorizations_active':False,'git_registry':registry,'public_cli_calls':sum(s.n for s in [source,target,other,many]),'source_selection_is_agent_policy':'Runtime discover returns candidates; Agent selected the unique or explicit fixture source per Skill. No native client interaction is claimed.'})
    print('Actual Git worktree unique/multiple source cloning passed',flush=True)

if __name__=='__main__':main()
