# GIF AI Hackathon 2026 — Round 1 Idea Submission

> Draft status: các giá trị định lượng bên dưới là mục tiêu cần kiểm chứng bằng benchmark/pilot, không phải kết quả đã được chứng minh tại FSOFT.

## 1. Tên ý tưởng/giải pháp

**TraceContract — Evidence-Grounded Context for Agentic Migration and Change**

TraceContract chuyển các artifact SDLC và source code theo phiên bản thành một trace graph được xác nhận, RTM có kiểm soát freshness, và executable context contract để AI coding agent thực hiện migration hoặc phát triển tính năng mới trên legacy system.

## 2. Hiện trạng/quy trình hiện tại

Khi tiếp nhận hoặc thay đổi một legacy system, delivery team thường có source code, Git history, user story và một phần tài liệu Architecture/Basic Design (BD)/Detail Design (DD), nhưng mức độ đầy đủ và cập nhật không đồng đều.

Quy trình phổ biến hiện nay gồm:

1. BA, Architect, Developer và Tester tìm kiếm thủ công trong tài liệu, source code và Git.
2. Team phỏng vấn người từng làm hệ thống và suy luận hành vi hiện tại từ code, test hoặc runtime.
3. Trace giữa requirement, design, code và test được lưu trong spreadsheet, ticket hoặc knowledge của từng cá nhân.
4. AI coding agent được dùng để đọc code, impact analysis, sinh code hoặc review. Tuy nhiên, agent thường phải khám phá lại context qua nhiều lần search/tool call, tiêu tốn token và thời gian.
5. Kết quả do agent tìm được chưa mặc nhiên có provenance, approval theo đúng role hoặc trạng thái freshness.
6. Reviewer phải tự kiểm tra lại evidence. Khi requirement, BD/DD hoặc code thay đổi, team khó biết trace nào đã stale và ai phải xác nhận lại.

Phạm vi mô tả trên là các delivery team xử lý legacy system; chưa đại diện cho toàn bộ quy trình của FSOFT nếu chưa có khảo sát nội bộ.

## 3. Bài toán nội bộ cần giải quyết

Các delivery team xử lý legacy system thiếu một cơ chế thống nhất để liên kết và duy trì bằng chứng giữa requirement, Architecture, BD, DD, code và test.

Vì vậy, AI agent có thể tạo thay đổi nhanh nhưng team vẫn khó trả lời bằng evidence:

- Behavior nào của hệ thống cũ phải được giữ, sửa hoặc loại bỏ?
- Requirement/design cụ thể được implement tại code symbol và LOC nào?
- Một đoạn business code tồn tại vì requirement nào và được test ở đâu?
- Tài liệu, code và test có còn nhất quán tại cùng một version không?
- Khi một artifact thay đổi, những trace và approval nào phải được kiểm tra lại?
- Implementation mới có bảo toàn các behavior đã được xác nhận và không gây regression trong phạm vi đã kiểm chứng không?

Nếu tiếp tục cho coding agent tự khám phá lại context ở từng task, thời gian, token và human review effort có thể tăng cùng với tốc độ sinh code.

## 4. Giải pháp hoạt động như thế nào

### A. Tạo evidence graph và certified RTM

1. **Ingest artifact:** đọc user story, Architecture, BD, DD, Git repository và test assets qua các adapter. Mỗi artifact được gắn version, hash và stable ID.
2. **Index code:** AI Workflow Agent sử dụng Codebase Memory MCP để lấy code symbols, source spans/LOC, call/import/test relationships, Git changes và runtime traces nếu có.
3. **Đề xuất trace:** Candidate Linker Agent kết hợp explicit ID, semantic retrieval, Git history, static graph và test/runtime evidence để đề xuất typed edges như `derived_into`, `implemented_by`, `verified_by`.
4. **Phân loại evidence:** candidate được xếp từ E0 Unknown đến E4 Executably Verified. AI confidence không được dùng thay cho approval.
5. **Review độc lập:** Forward Reviewer đi từ requirement xuống code/test; Reverse Reviewer đi từ code lên requirement/design; Adversarial Reviewer cố tìm counterexample hoặc evidence mâu thuẫn. Các reviewer chạy mù và không tự review output do chính mình tạo.
6. **Human verification:** BA, Architect, Tech Lead/Developer và QA xác nhận đúng loại artifact thuộc trách nhiệm của mình. Bất đồng phải có claim, evidence, rule và reproducer; nếu chưa phân xử được thì giữ trạng thái `disputed`.
7. **Deterministic certification:** RTM Validator kiểm tra graph invariants, role authority, artifact hashes, freshness và executable evidence. Certified RTM không chứa candidate hoặc high-risk stale edge chưa được xử lý.

### B. Migration một legacy module

8. **Compile Migration Context Contract:** hệ thống biên dịch verified requirements, approved as-is behavior, source symbols/LOC, contracts, tests, dependencies, contradictions và constraints thành context pack có cấu trúc cho coding agent.
9. **Build và review:** Migration Builder Agent tạo implementation mới. Các deterministic gates và reviewer độc lập kiểm tra requirement conformance, Architecture/BD/DD, behavioral equivalence, regression, security và test adequacy.
10. **Certify output:** mỗi component mới phải trace ngược về requirement/design và executable evidence trước khi được chứng nhận trong phạm vi verified behavior envelope.

### C. Phát triển feature mới trên legacy system

11. Requirement mới tạo một Change Context Contract gồm impacted Architecture/BD/DD claims, old-code symbols, test cần sửa/thêm và required approvals.
12. Agent chỉ sửa code sau khi hard prerequisites đủ. Sau thay đổi, affected subgraph được re-review; regression tests của feature cũ phải pass trước release.

### D. Duy trì consistency

Khi document hoặc code thay đổi, hệ thống tính affected subgraph. Trace liên quan tự chuyển `stale` và verification task được giao lại cho đúng role. Artifact không liên quan vẫn current, tránh review lại toàn hệ thống.

## 5. Điều kiện cần có để áp dụng

### Dữ liệu

- Git repository và commit history nếu có.
- Requirement/user story và các tài liệu Architecture, BD, DD hiện có.
- Test assets, build scripts và CI results; runtime traces là optional evidence.
- Stable project/repository identity và policy để phân loại dữ liệu.

### Hệ thống

- Local-first Evidence Core và graph store.
- Codebase Memory MCP qua một version-pinned adapter.
- Document adapters cho Markdown/text, structured JSON, DOCX và Jira export/API; XLSX dùng cho RTM import/export. PDF text là optional, scanned PDF/OCR ngoài MVP.
- Build/test sandbox và model endpoint được project policy cho phép.
- Canonical export loại timestamps/row IDs không ổn định, sort theo canonical key và hash từng artifact/evidence edge.

### Con người và quy trình

- BA/Product Owner xác nhận business requirement.
- Architect xác nhận Architecture/BD.
- Tech Lead/Developer xác nhận DD và code trace.
- QA xác nhận requirement-test và test adequacy.
- PM/Delivery Manager hoặc Engineering Manager sở hữu workflow.
- Quy định severity, waiver, approval expiry và release gate.

Giải pháp không yêu cầu tài liệu legacy phải hoàn hảo. Vùng thiếu, parser không hỗ trợ hoặc evidence không đủ phải được công khai là `unknown`, `unsupported` hoặc `partially_parsed`, không được suy diễn thành code rác.

## 6. AI được ứng dụng vào đâu và như thế nào

AI Agent là workflow orchestrator, không phải nguồn sự thật cuối cùng.

| Hoạt động | AI Agent | Deterministic system/human |
|---|---|---|
| Hiểu và phân rã tài liệu | Đề xuất atomic claims, contradictions và candidate links | Artifact owner xác nhận claim |
| Khám phá code | Lập kế hoạch và gọi Codebase Memory/search/Git/test tools | Adapter ghi provenance, version và coverage |
| Multi-hop trace | Chọn retrieval strategy và đề xuất trace path | Evidence Core lưu typed edge và trạng thái |
| Review | Forward/Reverse/Adversarial agents kiểm tra các khía cạnh độc lập | Hard gates và accountable role quyết định |
| Migration/change | Biên dịch context và coding agent sinh implementation | Hidden/acceptance/regression tests kiểm chứng |
| Freshness | Agent điều phối re-verification | Hash/diff/graph rule xác định stale |
| RTM | Agent giải thích và tìm gap | Canonical RTM được tạo bằng deterministic compiler |

Với cùng artifact snapshot, adapter versions và approved evidence, canonical RTM phải giống nhau qua các lần chạy. Câu chữ do LLM sinh và generated code không được cam kết byte-identical.

Evidence/source-derived knowledge được lưu trong local-first data plane. Model execution phụ thuộc deployment policy; nếu dùng cloud endpoint, chỉ context được cho phép mới được gửi và provider/model/context hash phải được audit. Giải pháp chưa tuyên bố mọi chức năng AI có thể chạy hoàn toàn offline.

Nguồn cảm hứng nghiên cứu:

- [Executable Code Knowledge: Code as a Native, Validation-Carrying Knowledge Representation for AI Coding Agents](https://arxiv.org/abs/2608.16295)
- [A Triple-Robustness Analysis of Retrieval-Augmented Generation for Multi-Hop Requirements Traceability](https://arxiv.org/abs/2608.00705)

## 7. Giá trị kinh doanh kỳ vọng

Giá trị kỳ vọng, cần được kiểm chứng bằng controlled benchmark và pilot nội bộ:

- Giảm effort tìm kiếm và xác minh context lặp lại giữa các migration/change tasks.
- Giảm token, tool calls và latency do coding/review agents phải khám phá lại cùng một codebase.
- Tăng trace completeness và khả năng tìm evidence gốc của mỗi quyết định.
- Phát hiện sớm missing behavior, contradiction, stale document và regression trong verified behavior envelope.
- Rút ngắn thời gian từ task đến approved implementation mà không bỏ qua governance.
- Giảm phụ thuộc vào knowledge của một cá nhân khi chuyển giao legacy system.
- Tái sử dụng certified evidence cho migration và các feature tiếp theo.

Không đưa ra con số tiết kiệm trước khi đo. Pilot sẽ so sánh cùng model, tools và budget giữa:

```text
Baseline: raw documents + repository + Codebase Memory
Treatment: cùng input + verified TraceContract
```

Primary metric là hidden acceptance/regression test pass rate trong budget cố định. Secondary metrics gồm end-to-end time, human verification minutes, token/tool-call cost, số vòng sửa, trace completeness và reviewer findings.

Business value được tính theo hai góc nhìn:

```text
Cold-start cost
= ingest + link + human verification + implementation

Steady-state change cost
= impact analysis + affected-subgraph re-verification + implementation
```

Nếu treatment không cải thiện migration conformance hoặc không giảm net effort sau khi tính human review, claim "migration accelerator" không được xem là đã chứng minh.

