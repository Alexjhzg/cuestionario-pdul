export interface ProblemDetailOut {
  code: string;
  title: string;
  status: number;
  detail: string;
  field?: string | null;
  errors?: Array<Record<string, unknown>> | null;
}

export interface SubmissionReceiptOut {
  id: number;
  fecha_registro: string;
  idempotent_replay: boolean;
  mensaje: string;
}

