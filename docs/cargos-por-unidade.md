# Gestor, Controller e Colaborador: qual cargo dar em cada unidade

13/11/2026 · Documento original: https://claude.ai/artifact/4yyXES2wKsWiKrhpaRZ3px

## Resumo

O cargo de uma pessoa em cada unidade segue **o que ela faz naquela unidade**, não o domínio do e-mail. O e-mail diz para qual escritório ela trabalha; o cargo diz o que ela vê e pode fazer em cada unidade. Controller dá **mais** visão que Colaborador, não menos.

No caso da Nayla Brazão, trocar para Controller na LARJ **só faz sentido se o trabalho dela for acompanhar todos os indicadores da LARJ**. Se ela atende o Comercial da LARJ, o certo é continuar Colaboradora na equipe Comercial de lá, como está hoje.

## Os cargos por unidade

Desde 13/11, Gestor cuida da unidade e Controller acompanha. Antes os dois tinham as mesmas permissões, por isso se confundiam.

| Cargo | Dashboards da unidade | Exportar | Fontes | Membros e acesso | Para quem |
| --- | --- | --- | --- | --- | --- |
| Gestor | Todos | Tudo | Vê | Gere | Quem responde pelas pessoas da unidade |
| Controller | Todos | Tudo | Vê | Não | Quem acompanha os números da unidade inteira |
| Colaborador | Os que as equipes dele liberam | Só do próprio setor | Não | Não | Quem trabalha num setor da unidade |
| Leitor | Os que as equipes dele liberam, só resumos | Não | Não | Não | Quem só consulta |

O cargo vale **por unidade**: a mesma pessoa pode ser Gestor numa e Controller ou Colaborador em outra. Owner e Desenvolvedor ficam acima disso e veem todas as unidades.

## A regra: o cargo segue o trabalho, não o e-mail

Para cada unidade em que a pessoa aparece, responda na ordem e pare na primeira resposta "sim":

1. Ela responde pelas pessoas dessa unidade (convida, desativa, muda cargos)? → **Gestor**
2. Ela precisa ver os números da unidade inteira, de todos os setores? → **Controller**
3. Ela trabalha num setor dessa unidade? → **Colaborador**, nas equipes desse setor
4. Ela só consulta resumos? → **Leitor**
5. Nenhuma das anteriores → **sem cargo** nessa unidade

Três cuidados:

- **O domínio do e-mail não decide o cargo.** Ele mostra o empregador. Quem trabalha para dois escritórios tem um cargo em cada um, de acordo com o que faz em cada.
- **Controller não é um cargo "menor".** Trocar Colaborador por Controller abre todos os dashboards da unidade e a exportação de todos os setores.
- **Dê o menor cargo que resolve o trabalho.** Se uma equipe já libera o que a pessoa precisa, Colaborador basta.

## Caso de teste: Nayla Brazão

Hoje a Nayla é Colaboradora na equipe Comercial em duas unidades. O e-mail dela é do domínio da Nicolas Gomes.

| Unidade | Cargo hoje | Equipe | O que ela vê |
| --- | --- | --- | --- |
| NICOLAS GOMES (NG) | Colaborador | Comercial | Os dashboards que o Comercial libera; exporta só o Comercial |
| LARJ (RJ) | Colaborador | Comercial | Os dashboards que o Comercial libera; exporta só o Comercial |

Na NG a regra confirma o cargo atual: ela trabalha no Comercial, então é Colaboradora. Na LARJ, a resposta depende do que ela faz lá:

| Se na LARJ ela… | Cargo certo na LARJ | O que muda para ela |
| --- | --- | --- |
| Atende o Comercial da LARJ (mesmo trabalho da NG, em outra carteira) | Colaborador, equipe Comercial | Nada: é o cargo de hoje |
| Acompanha os números da LARJ inteira (todos os setores) | Controller | Passa a ver todos os dashboards da LARJ e a exportar todos os setores |
| Só consulta os resultados comerciais da LARJ de vez em quando | Leitor, equipe Comercial | Perde a exportação e passa a ver só resumos |
| Não faz nada pela LARJ | Sem cargo | Deixa de ver a LARJ |

A leitura mais provável é a primeira. Ela está na **mesma equipe** nas duas unidades, e a LARJ usa a base de dados da NG. Isso sugere que ela faz o Comercial das duas carteiras. Nesse caso, virar Controller daria a ela mais acesso do que o trabalho pede.

Para testar a regra no sistema com a Nayla:

- [ ] Entrar como Nayla e conferir que, na LARJ, ela vê só os dashboards do Comercial
- [ ] Conferir que ela não vê Membros nem Acesso no menu
- [ ] Se a gestão decidir por Controller na LARJ: mudar o cargo na aba Acesso e conferir que ela passa a ver todos os dashboards da LARJ, mas continua sem Membros e Acesso

## Como aplicar e o que confirmar

Quem muda o cargo é o Owner, um Desenvolvedor ou o Gestor da unidade, na aba **Acesso**: escolha a unidade, abra a pessoa, troque o cargo só naquela unidade e salve. Ninguém muda o próprio cargo, e o Controller não muda cargos de ninguém.

Perguntas para a gestão:

- O que a Nayla faz pela LARJ: atende o Comercial de lá ou acompanha a unidade inteira?
- Amanda Carvalho, Beatriz Castro e Marcela Luz são Gestoras em LAAM e LARJ. Elas respondem pelas pessoas das duas unidades, ou só de uma e acompanham a outra (Controller)?
- Hoje ninguém é Controller. Quem deveria ser?
