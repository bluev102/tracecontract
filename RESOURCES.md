# TraceContract Resources

## Knowledge

- [Paper: _Executable Code Knowledge_ — Xueping Gao](https://arxiv.org/abs/2608.16295)
  Nguồn trực tiếp cho source-bound identity, executable evidence, validation state, exact changed-line impact và freshness. Dùng để thiết kế code artifact/evidence; không dùng để khẳng định end-to-end migration đã được chứng minh.
- [Paper: _A Triple-Robustness Analysis of RAG for Multi-Hop Requirements Traceability_ — Akarsu et al.](https://arxiv.org/abs/2608.00705)
  Nguồn trực tiếp cho giới hạn của GraphRAG, sự khác nhau giữa retrieved context và cited evidence, và độ bất ổn của single-LLM judge. Dùng để đặt AI ở candidate/review layer thay vì authority layer.
- [W3C PROV Model Primer](https://www.w3.org/TR/prov-primer/)
  Mô hình chuẩn về Entity, Activity, Agent, derivation và responsibility. Dùng làm nền cho provenance/audit schema thay vì tự phát minh toàn bộ vocabulary.
- [W3C PROV-O Recommendation](https://www.w3.org/TR/prov-o/)
  Ontology chuẩn, mở rộng được cho trao đổi provenance. Dùng khi cần map data model nội bộ sang vocabulary có tính liên vận; MVP không bắt buộc dùng RDF/OWL.
- [SLSA v1.2: Provenance](https://slsa.dev/spec/v1.2/provenance)
  Định nghĩa provenance có thể kiểm chứng về nơi, lúc và cách software artifact được tạo. Dùng để phân biệt trace ngữ nghĩa với build/source provenance.
- [NIST: Software Supply Chain Security Terminology](https://www.nist.gov/itl/executive-order-14028-improving-nations-cybersecurity/software-supply-chain-security-guidance-10)
  Phân biệt artifact, evidence, attestation và conformity. Dùng để thiết kế certification language và tránh gọi một link do AI đề xuất là “proof”.
- [Repository document: Technical Blueprint](technical-blueprint.md)
  Đặc tả nội bộ hiện tại về system boundary, canonical model, review topology, freshness và MVP.
- [Repository document: Scientific Validation Plan](validation-plan.md)
  Các giả thuyết falsifiable, benchmark fixture, hidden tests và controlled A/B design của TraceContract.

## Wisdom (Communities)

- [Requirements Engineering Stack Exchange](https://pm.stackexchange.com/)
  Nơi kiểm tra các quyết định thực hành về requirement lifecycle và traceability với cộng đồng quản lý dự án/phân tích yêu cầu.
- [SLSA community](https://slsa.dev/community)
  Nơi đối chiếu các lựa chọn provenance/attestation với người triển khai software supply-chain assurance.

## Gaps

- Chưa có khảo sát nội bộ FSOFT chứng minh pain point, mức effort hiện tại hoặc willingness-to-adopt.
- Chưa có nguồn gold hoàn chỉnh cho trace Architecture/BD/DD → symbol/LOC; phần này phải benchmark-author và review độc lập.
- Chưa hoàn tất feasibility gate để chứng minh iTrust2 v7/v8 build/test lặp lại được trong môi trường cô lập.
