/**
 * Lista canónica de campos de identificación personal (PII) protegidos
 * tanto en analítica backend como en enmascaramiento de auditoría frontend.
 */
export const PII_FIELDS = [
  'cedula',
  'nombre_apellido',
  'nombres_apellidos',
  'nombre',
  'apellido',
  'telefono',
  'correo',
  'email',
  'casa_apartamento',
  'avenida_calle',
  'direccion_exacta'
] as const;

export type PiiFieldName = (typeof PII_FIELDS)[number];

export const PII_FIELD_SET: ReadonlySet<string> = new Set(PII_FIELDS);

