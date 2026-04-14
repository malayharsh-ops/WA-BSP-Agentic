-- Seed: sample leads and a demo campaign

INSERT INTO leads (id, phone, name, language, stage, score, project_type, project_location, material_needed, volume_mt)
VALUES
  ('00000000-0000-0000-0000-000000000001', '919876543210', 'Ramesh Kumar', 'hi', 'HOT', 85, 'commercial', 'Mumbai', 'TMT Fe500', '100'),
  ('00000000-0000-0000-0000-000000000002', '919876543211', 'Suresh Patel', 'gu', 'WARM', 45, 'residential', 'Ahmedabad', 'TMT Fe415', '20'),
  ('00000000-0000-0000-0000-000000000003', '919876543212', 'Anjali Rao', 'en', 'NEW', 10, NULL, 'Bengaluru', NULL, NULL)
ON CONFLICT (phone) DO NOTHING;

INSERT INTO campaigns (id, name, template_name, language, status)
VALUES
  ('00000000-0000-0000-0000-000000000010', 'Monsoon TMT Offer', 'jsw_tmt_offer_v1', 'hi', 'DRAFT'),
  ('00000000-0000-0000-0000-000000000011', 'Cement Bundle April', 'jsw_cement_bundle_v1', 'en', 'DRAFT')
ON CONFLICT DO NOTHING;
