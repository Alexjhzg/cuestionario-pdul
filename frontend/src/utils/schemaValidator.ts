/**
 * Validador de esquemas JSON Form.io para el Constructor de Encuestas
 * Asegura compatibilidad con validate_formio_schema.py y soberanía de datos
 */

const SNAKE_CASE_RE = /^[a-z][a-z0-9_]*$/;
const FORBIDDEN_HOSTS = ['form.io', 'googleapis.com', 'mapbox.com', 'amazonaws.com'];

export interface SchemaValidationResult {
  valid: boolean;
  errors: string[];
}

export function validateFormioSchema(
  schema: Record<string, any>,
  options: { requireSubmit?: boolean; requireParroquia?: boolean } = {}
): SchemaValidationResult {
  const errors: string[] = [];
  const { requireSubmit = true, requireParroquia = false } = options;

  if (!schema || typeof schema !== 'object') {
    return { valid: false, errors: ['El esquema debe ser un objeto JSON válido'] };
  }

  if (!Array.isArray(schema.components)) {
    return { valid: false, errors: ['El esquema debe contener un arreglo "components"'] };
  }

  let hasSubmitButton = false;
  let hasParroquia = false;

  function walkComponents(components: any[], path: string, scopeKeys: Set<string>) {
    for (let i = 0; i < components.length; i++) {
      const comp = components[i];
      if (!comp || typeof comp !== 'object') {
        errors.push(`[${path}[${i}]] El componente no es un objeto válido`);
        continue;
      }

      const ctype = comp.type;
      const key = comp.key;

      if (!ctype) {
        errors.push(`[${path}[${i}]] Falta la propiedad "type"`);
      }

      if (key) {
        if (!SNAKE_CASE_RE.test(key)) {
          errors.push(`[${path}] La clave "${key}" debe usar snake_case ASCII minúsculas`);
        }
        if (scopeKeys.has(key) && !['panel', 'htmlelement', 'content'].includes(ctype)) {
          errors.push(`[${path}] Clave duplicada en el mismo ámbito: "${key}"`);
        }
        scopeKeys.add(key);

        if (key === 'parroquia') {
          hasParroquia = true;
        }
      }

      // Comprobar botón submit
      if (ctype === 'button' && comp.action === 'submit') {
        hasSubmitButton = true;
      }

      // Comprobar URLs prohibidas
      const jsonStr = JSON.stringify(comp);
      for (const host of FORBIDDEN_HOSTS) {
        if (jsonStr.includes(host)) {
          errors.push(`[${path}] Se detectó URL o referencia a servicio externo no soberano: ${host}`);
        }
      }

      // Recursión en contenedores anidados
      const nestedScopeKeys = new Set<string>();
      if (Array.isArray(comp.components)) {
        walkComponents(comp.components, `${path}.${key || ctype}`, nestedScopeKeys);
      }
      if (Array.isArray(comp.columns)) {
        for (let colIdx = 0; colIdx < comp.columns.length; colIdx++) {
          const col = comp.columns[colIdx];
          if (Array.isArray(col.components)) {
            walkComponents(col.components, `${path}.${key || ctype}.col${colIdx}`, nestedScopeKeys);
          }
        }
      }
      if (Array.isArray(comp.rows)) {
        for (let rIdx = 0; rIdx < comp.rows.length; rIdx++) {
          const row = comp.rows[rIdx];
          if (Array.isArray(row)) {
            for (let cIdx = 0; cIdx < row.length; cIdx++) {
              if (Array.isArray(row[cIdx]?.components)) {
                walkComponents(row[cIdx].components, `${path}.${key}.row${rIdx}col${cIdx}`, nestedScopeKeys);
              }
            }
          }
        }
      }
    }
  }

  walkComponents(schema.components, 'root', new Set<string>());

  if (requireSubmit && !hasSubmitButton) {
    errors.push('El formulario debe contener al menos un botón con acción "submit"');
  }

  if (requireParroquia && !hasParroquia) {
    errors.push('El esquema debe incluir el campo geográfico "parroquia"');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}
