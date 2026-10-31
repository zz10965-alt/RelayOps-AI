from pathlib import Path
required=['AGENTS.md','PLANS.md','PRD.md','ARCHITECTURE.md','API_SPEC.md','workflow_design.md','evaluation_plan.md','progress/build-log.md','README.md']
for name in required:
    assert Path(name).is_file() and Path(name).stat().st_size>100, name
assert Path('docs/project-instructions.md').stat().st_size==6812
assert '真实 Dify' in Path('README.md').read_text()
print(f'Document checks passed: {len(required)} files + original instruction length')
