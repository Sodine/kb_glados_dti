create extension if not exists pgcrypto;

create table if not exists bot_atendimento_ti.usuarios_painel (
  id uuid primary key default gen_random_uuid(),
  usuario text not null unique,
  senha_hash text not null,
  pode_ler boolean not null default true,
  pode_criar boolean not null default false,
  pode_editar boolean not null default false,
  pode_excluir boolean not null default false,
  pode_gerenciar_usuarios boolean not null default false,
  ativo boolean not null default true,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

do $$
begin
  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'bot_atendimento_ti'
      and table_name = 'usuarios_painel'
      and column_name = 'username'
  ) then
    alter table bot_atendimento_ti.usuarios_painel rename column username to usuario;
  end if;

  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'bot_atendimento_ti'
      and table_name = 'usuarios_painel'
      and column_name = 'password_hash'
  ) then
    alter table bot_atendimento_ti.usuarios_painel rename column password_hash to senha_hash;
  end if;

  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'bot_atendimento_ti'
      and table_name = 'usuarios_painel'
      and column_name = 'can_read'
  ) then
    alter table bot_atendimento_ti.usuarios_painel rename column can_read to pode_ler;
  end if;

  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'bot_atendimento_ti'
      and table_name = 'usuarios_painel'
      and column_name = 'can_create'
  ) then
    alter table bot_atendimento_ti.usuarios_painel rename column can_create to pode_criar;
  end if;

  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'bot_atendimento_ti'
      and table_name = 'usuarios_painel'
      and column_name = 'can_edit'
  ) then
    alter table bot_atendimento_ti.usuarios_painel rename column can_edit to pode_editar;
  end if;

  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'bot_atendimento_ti'
      and table_name = 'usuarios_painel'
      and column_name = 'can_delete'
  ) then
    alter table bot_atendimento_ti.usuarios_painel rename column can_delete to pode_excluir;
  end if;

  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'bot_atendimento_ti'
      and table_name = 'usuarios_painel'
      and column_name = 'can_manage_users'
  ) then
    alter table bot_atendimento_ti.usuarios_painel rename column can_manage_users to pode_gerenciar_usuarios;
  end if;

  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'bot_atendimento_ti'
      and table_name = 'usuarios_painel'
      and column_name = 'is_active'
  ) then
    alter table bot_atendimento_ti.usuarios_painel rename column is_active to ativo;
  end if;

  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'bot_atendimento_ti'
      and table_name = 'usuarios_painel'
      and column_name = 'created_at'
  ) then
    alter table bot_atendimento_ti.usuarios_painel rename column created_at to criado_em;
  end if;

  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'bot_atendimento_ti'
      and table_name = 'usuarios_painel'
      and column_name = 'updated_at'
  ) then
    alter table bot_atendimento_ti.usuarios_painel rename column updated_at to atualizado_em;
  end if;
end;
$$;

create or replace function bot_atendimento_ti.definir_atualizado_em()
returns trigger
language plpgsql
as $$
begin
  new.atualizado_em = now();
  return new;
end;
$$;

drop trigger if exists usuarios_painel_set_updated_at on bot_atendimento_ti.usuarios_painel;
drop trigger if exists usuarios_painel_definir_atualizado_em on bot_atendimento_ti.usuarios_painel;

create trigger usuarios_painel_definir_atualizado_em
before update on bot_atendimento_ti.usuarios_painel
for each row
execute function bot_atendimento_ti.definir_atualizado_em();
