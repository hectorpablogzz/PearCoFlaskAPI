-- Habilitar generación de UUID
create extension if not exists "pgcrypto";

-- Limpieza previa (opcional)
drop table if exists TerminosCondiciones, Fotos, UsuarioAlerta, UsuarioEnfermedad, Reportes,
Usuarios, Enfermedad, Alertas, TipoAlerta, Parcela, Ubicacion cascade;

-- =====================================
-- TABLA: Ubicacion
-- =====================================
create table Ubicacion (
    IdUbicacion uuid primary key default gen_random_uuid(),
    Estado varchar(100) not null,
    Municipio varchar(100) not null,
    Latitud double precision,
    Longitud double precision
);

-- =====================================
-- TABLA: Parcela
-- =====================================
create table Parcela (
    IdParcela uuid primary key default gen_random_uuid(),
    Nombre varchar(100) not null,
    Hectareas double precision,
    Tipo varchar(50),
    IdUbicacion uuid references Ubicacion(IdUbicacion) on delete set null
);

-- =====================================
-- TABLA: TipoAlerta
-- =====================================
create table TipoAlerta (
    IdTipoAlerta uuid primary key default gen_random_uuid(),
    Tipo varchar(100) not null
);

-- =====================================
-- TABLA: Alertas
-- =====================================
create table Alertas (
    IdAlerta uuid primary key default gen_random_uuid(),
    IdTipoAlerta uuid references TipoAlerta(IdTipoAlerta) on delete cascade,
    Titulo varchar(100),
    Descripcion varchar(200)
);

-- =====================================
-- TABLA: Enfermedad
-- =====================================
create table Enfermedad (
    IdEnfermedad uuid primary key default gen_random_uuid(),
    Descripcion text,
    Causas text,
    Prevencion text,
    Tratamiento text
);

-- =====================================
-- TABLA: Usuarios
-- =====================================
create table Usuarios (
    IdUsuario uuid primary key default gen_random_uuid(),
    Nombre varchar(100) not null,
    Apellido varchar(100) not null,
    Correo varchar(100) unique not null,
    Contrasena varchar(100) not null, -- evita caracteres especiales en identificadores
    IdParcela uuid references Parcela(IdParcela) on delete set null,
    IdTipoUsuario int
);

-- =====================================
-- TABLA: UsuarioEnfermedad (N:M)
-- =====================================
create table UsuarioEnfermedad (
    IdUsuario uuid references Usuarios(IdUsuario) on delete cascade,
    IdEnfermedad uuid references Enfermedad(IdEnfermedad) on delete cascade,
    primary key (IdUsuario, IdEnfermedad)
);

-- =====================================
-- TABLA: UsuarioAlerta (N:M)
-- =====================================
create table UsuarioAlerta (
    IdUsuario uuid references Usuarios(IdUsuario) on delete cascade,
    IdAlerta uuid references Alertas(IdAlerta) on delete cascade,
    Completado boolean default false,
    primary key (IdUsuario, IdAlerta)
);

-- =====================================
-- TABLA: Reportes
-- =====================================
create table Reportes (
    IdReporte uuid primary key default gen_random_uuid(),
    IdUsuario uuid references Usuarios(IdUsuario) on delete cascade,
    IdEnfermedad uuid references Enfermedad(IdEnfermedad) on delete cascade,
    Recomendacion text,
    Fecha timestamptz default now(),
    Descripcion text,
    Graficas boolean default false
);

-- =====================================
-- TABLA: Fotos
-- =====================================
create table Fotos (
    IdFoto uuid primary key default gen_random_uuid(),
    IdUsuario uuid references Usuarios(IdUsuario) on delete cascade,
    Foto text  -- si es URL/base64, text es más flexible que varchar(200)
);

-- =====================================
-- TABLA: TerminosCondiciones
-- =====================================
create table TerminosCondiciones (
    IdUsuario uuid primary key references Usuarios(IdUsuario) on delete cascade,
    Version varchar(50),
    FechaAceptacion timestamptz default now()
);

-- Índices sugeridos (performance en joins por FK)
create index if not exists idx_parcela_idubicacion on Parcela (IdUbicacion);
create index if not exists idx_alertas_idtipo on Alertas (IdTipoAlerta);
create index if not exists idx_usuarios_idparcela on Usuarios (IdParcela);
create index if not exists idx_usuarioenfermedad_usuario on UsuarioEnfermedad (IdUsuario);
create index if not exists idx_usuarioenfermedad_enfermedad on UsuarioEnfermedad (IdEnfermedad);
create index if not exists idx_usuarioalerta_usuario on UsuarioAlerta (IdUsuario);
create index if not exists idx_usuarioalerta_alerta on UsuarioAlerta (IdAlerta);
create index if not exists idx_reportes_usuario on Reportes (IdUsuario);
create index if not exists idx_reportes_enfermedad on Reportes (IdEnfermedad);
create index if not exists idx_fotos_usuario on Fotos (IdUsuario);