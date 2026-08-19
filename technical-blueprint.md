# TraceContract — Technical Blueprint

## 1. Research origin

TraceContract bắt đầu từ hai hướng nghiên cứu bổ sung nhau. Hai paper là nền tảng tham chiếu, không phải bằng chứng rằng toàn bộ TraceContract đã được kiểm chứng.

### 1.1 Executable Code Knowledge

[Executable Code Knowledge: Code as a Native, Validation-Carrying Knowledge Representation for AI Coding Agents](https://arxiv.org/abs/2608.16295) đề xuất biểu diễn một số code unit quan trọng như knowledge unit gắn với identity, semantics, executable body, contract, evidence, provenance và freshness.

Những ý tưởng được kế thừa:

- Code knowledge phải gắn với source span/hash thay vì chỉ là prose trong vector store.
- Evidence có thể thực thi và freshness phải là first-class state.
- Coding agent nên nhận task-specific context/evidence thay vì đọc một knowledge dump không kiểm soát.
- Git diff có thể được đối chiếu với registered source span để tìm direct impact một cách deterministic.

Giới hạn phải giữ nguyên khi viện dẫn paper:

- Prototype và thí nghiệm chủ yếu ở Python, trên số lượng code unit/repository nhỏ.
- Direct impact trong paper là source-span intersection, không chứng minh semantic/transitive impact tổng quát.
- Annotation sai hoặc evidence cũ vẫn có thể làm agent hiểu sai.
- Paper không giải quyết requirement/Architecture/BD/DD graph, role-based approval hoặc end-to-end migration.

TraceContract mở rộng hướng này từ code unit sang versioned SDLC artifacts và typed trace edges, nhưng phần mở rộng phải được đánh giá độc lập.

### 1.2 Triple-Robustness RAG for Multi-Hop Requirements Traceability

[A Triple-Robustness Analysis of Retrieval-Augmented Generation for Multi-Hop Requirements Traceability](https://arxiv.org/abs/2608.00705) so sánh vanilla, agentic, graph-assisted và adaptive retrieval cho traceability queries nhiều hop.

Những ý tưởng được kế thừa:

- Typed graph phù hợp cho các đường trace nhiều tầng.
- Retrieval strategy phải phụ thuộc query/corpus; GraphRAG không mặc nhiên tốt nhất cho mọi query.
- Phải tách retrieved context khỏi evidence thực sự được citation trong output.
- Một LLM judge đơn lẻ không đủ ổn định để làm nguồn nghiệm thu.
- Multi-hop retrieval có thể tăng recall nhưng cũng kéo thêm context nhiễu.

Giới hạn phải giữ nguyên:

- Requirements corpus chính của paper là synthetic; kết quả không trực tiếp chứng minh hiệu quả trên dữ liệu FSOFT.
- Router và kiến trúc GraphRAG cụ thể chưa phải production guarantee.
- Paper không map tới code symbol/LOC, không quản lý human approval/freshness và không đánh giá migration outcome.

TraceContract sử dụng LLM/RAG cho candidate discovery và explanation; verified graph cùng deterministic compiler mới là authority.

### 1.3 Phần đóng góp cần kiểm chứng của TraceContract

TraceContract kết hợp và mở rộng hai hướng trên bằng:

1. Versioned graph nối Requirement → Architecture → BD → DD → Code Symbol/LOC → Test.
2. Candidate/verified/rejected/stale/disputed lifecycle và approval theo accountable role.
3. Forward, reverse và adversarial RTM review độc lập.
4. Deterministic canonical RTM compiler.
5. Compilation từ certified evidence sang Migration/Change Context Contract cho coding agent.
6. Controlled evaluation từ trace quality tới migration correctness và total engineering effort.

Đây là proposed system contribution, chưa phải research result.

## 2. System boundary

```text
                       AI Workflow Agent
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
Document Adapters     Codebase Memory MCP      Build/Test Tools
MD/DOCX/Jira/XLSX     code intelligence        CI/coverage/runtime
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                    Candidate Linker Agent
                              │
                              ▼
                    RTM Evidence Core MCP
             canonical artifacts, typed trace edges,
             evidence, approval, freshness, audit log
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
          Forward          Reverse         Adversarial
          Reviewer         Reviewer         Reviewer
              └───────────────┼────────────────┘
                              ▼
                 Deterministic RTM Validator
                              │
                              ▼
               Migration/Change Context Compiler
                              │
                              ▼
                    Coding/Migration Agent
```

## 3. Responsibility boundaries

### 3.1 Codebase Memory MCP

Codebase Memory cung cấp observed code facts/candidates:

- Repository indexing và code graph.
- Class/function/method/resource symbols và source spans.
- Call/import/implements/tests relationships.
- Search, trace path, architecture view và code snippets.
- Change detection và optional runtime trace ingestion.

Tham chiếu: [Codebase Memory MCP](https://github.com/DeusData/codebase-memory-mcp).

Nó không phải RTM authority. Adapter phải bổ sung:

```text
repo_id
commit_sha
provider_name/provider_version
adapter_config_hash
qualified_symbol
normalized_symbol_hash
start_line/end_line
index_coverage
raw_result_hash
```

Không đọc/ghi trực tiếp SQLite nội bộ làm integration contract. Pin exact provider version và gọi qua MCP/export. Nếu parser thiếu coverage, state phải là `unsupported`, `partially_parsed`, `excluded` hoặc `unknown`; không được kết luận `orphaned/dead`.

### 3.2 Evidence Core

Evidence Core là system of record cho:

- Canonical artifacts và versions.
- Typed trace edges.
- Evidence bundles và provenance.
- Candidate/review/approval state machine.
- Role/permission policy.
- Freshness propagation.
- Conflict, waiver và audit history.
- Canonical RTM export.

### 3.3 AI agents

Agents được phép:

- Lập kế hoạch gọi document/code/Git/test tools.
- Đề xuất atomic claims và candidate traces.
- Tìm contradiction/gaps/counterexamples.
- Soạn context contract và implementation.
- Route verification tasks.

Agents không được phép:

- Tự thăng edge do mình đề xuất thành verified.
- Sửa gold evidence hoặc hidden tests để làm output pass.
- Che giấu unknown/index gaps.
- Biến LLM confidence thành probability of correctness.
- Ghi trực tiếp vào certified RTM ngoài deterministic workflow.

## 4. Canonical data model

### 4.1 Artifact identity

```text
ArtifactKey = project_id + artifact_type + canonical_id + version_hash

CodeArtifactKey = repo_id + commit_sha + adapter_version
                + qualified_symbol + normalized_symbol_hash
```

LOC là presentation evidence tại một commit, không phải long-lived identity.

### 4.2 Artifact types

- Requirement/User Story/Acceptance Criterion.
- Architecture Decision/Constraint/Component.
- Basic Design Claim.
- Detail Design Claim.
- Code Symbol/Source Span.
- Test Specification/Test Case/Test Result.
- Runtime Observation.
- Migration/Change Unit.
- Human Approval/Waiver.

### 4.3 Edge types

```text
derived_into
constrained_by
detailed_by
implemented_by
verified_by
depends_on
calls/imports/implements
migrates_to
supersedes
contradicts
approved_by
```

### 4.4 Edge state

```text
candidate → verified
          → rejected

verified → stale → reverified/rejected

any reviewable state → disputed
```

Mỗi edge giữ origin, evidence references, endpoint hashes, proposer, reviewers, approver, timestamps, policy version và status reason.

### 4.5 Evidence maturity

| Class | Meaning |
|---|---|
| E0 Unknown | Evidence thiếu hoặc index không đầy đủ |
| E1 Candidate | AI đề xuất, chưa corroborate/approve |
| E2 Corroborated | Có ít nhất hai loại evidence độc lập; chưa có accountable approval |
| E3 Verified | Đúng role xác nhận trên current artifact versions |
| E4 Executably Verified | E3 cộng executable evidence pass tại đúng commit/environment |

`stale`, `disputed`, `partially_parsed` là orthogonal state, không phải một bậc điểm số.

## 5. Review topology

### Candidate Linker

Tối ưu recall; tìm rộng bằng explicit IDs, retrieval, code graph, Git, test và runtime evidence. Output luôn là candidate.

### Forward Trace Reviewer

Đi từ requirement xuống design, implementation và test. Tìm missing/partial implementation, missing test và acceptance criteria chưa được phủ.

### Reverse Trace Reviewer

Đi từ changed/new business code ngược lên design/requirement. Tìm untraced behavior, speculative code, scope creep và legacy behavior chưa có quyết định.

### Adversarial Trace Reviewer

Cố bác bỏ link/claim bằng contradiction, stale evidence, boundary/negative case, dynamic dispatch, misleading test hoặc concrete counterexample.

### Deterministic RTM Validator

Không dùng LLM để kiểm tra:

- Schema và stable IDs.
- Endpoint hashes/freshness.
- Mandatory graph paths.
- Approval authority.
- Candidate/stale/disputed policy.
- Executable evidence binding.
- Canonical ordering/export.

### Human accountability

| Trace/artifact | Accountable role |
|---|---|
| Business requirement | Product Owner/BA |
| Architecture/BD | Architect, BA where applicable |
| DD/code trace | Tech Lead/Developer |
| Requirement-test/test adequacy | BA/QA |
| Retire/rewrite decision | Tech Lead/System Owner |

## 6. Conflict protocol

1. Chuẩn hóa verdict về cùng claim và artifact version.
2. Loại verdict thiếu evidence hoặc dùng stale artifact.
3. Chạy deterministic reproducer/test nếu có.
4. Một valid counterexample bác bỏ universal claim.
5. Nếu chưa phân xử được, giữ `disputed` và route tới accountable role.

Không majority-vote correctness. Majority chỉ có thể dùng cho preference/advisory decisions.

## 7. Freshness and consistency

Artifact change không invalid toàn bộ graph. Policy tính typed affected subgraph:

```text
Requirement change
→ related Architecture/BD/DD trace stale
→ linked code/test evidence requires review
→ dependent components examined
```

Nếu evidence không đủ giới hạn impact radius, state phải là `impact_boundary_uncertain` và review scope được mở rộng.

Canonical RTM repeatability áp dụng khi repo commit, documents, adapter/parser versions, configuration và approved evidence giống nhau. Timestamps, database row IDs và generated prose bị loại khỏi canonical representation.

## 8. Context contracts

### Migration Context Contract

- Verified requirements.
- Approved as-is behaviors.
- Source symbols/spans/hashes.
- Architecture/BD/DD claims.
- Input/output contracts và business invariants.
- Executable tests/evidence.
- Dependencies/impact radius.
- Known contradictions/unknowns.
- Forbidden/deprecated behaviors.
- Required approvals.

### Change Context Contract

- New/changed requirement.
- Impacted Architecture/BD/DD claims.
- Impacted old/new code symbols.
- Tests phải sửa/thêm.
- Regression surface.
- Required reviews và release gates.

## 9. Deployment and security boundary

- Evidence DB, source index và canonical RTM nằm trong local-first data plane.
- Model execution là policy-configurable; MVP không claim fully offline inference.
- Cloud egress phải được allowlist theo project classification và gửi minimal context.
- Audit provider, model, prompt/config và context hash.
- Tắt cloud embeddings hoặc dùng local provider khi policy cấm source-derived text rời môi trường.
- Enforce source/document ACL trước retrieval, không chỉ trước UI rendering.

## 10. MVP boundary

Primary scenario: iTrust2 v7 UC19 Food Diary được khôi phục vào v8 Spring Boot, sau đó thêm date-range nutrition summary và chạy regression suite.

MVP target:

- 5–10 requirement/acceptance claims.
- Architecture/BD/DD benchmark artifacts có provenance.
- 20–50 relevant code symbols.
- 10–20 executable/hidden tests.
- 3–5 known inconsistencies.
- Một migration unit và một subsequent feature change.

Out of scope:

- Chứng minh mọi ngôn ngữ/framework.
- Fully autonomous approval.
- Zero-regression guarantee.
- Scanned PDF/OCR.
- Production deployment toàn công ty.
- Tự kết luận/xóa dead code.

