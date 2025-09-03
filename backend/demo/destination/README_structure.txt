Expected destination folder structure:

DEST_ROOT/
├── <document_form>/          (e.g., contract, NDA, service_agreement)
    ├── <client_name>/        (e.g., StartupAlpha, TechCorp)
        ├── <date>/           (e.g., 2024-08-21, 20240815)
            └── <status>/     (e.g., signed, executed, final)
                └── actual_files.pdf

Examples:
- contract/StartupAlpha/2024-08-21/signed/contract_StartupAlpha_2024-08-21_signed.pdf
- NDA/TechCorp/20240815/executed/NDA_TechCorp_20240815_executed.pdf
- service_agreement/ClientBeta/2024-07-30/final/service_agreement_ClientBeta_2024-07-30_final.pdf