export interface ParroquiaCatalogItem {
  codigo: string;
  value: string;
  nombre: string;
  label: string;
  tipo: string;
  capital: string;
}

export interface CatalogOptionItem {
  codigo: string;
  value: string;
  nombre: string;
  label: string;
}

export interface RutaTransporteCatalogItem extends CatalogOptionItem {
  modalidades: string[];
  tipos_vehiculo: string[];
}

