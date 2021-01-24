--
-- PostgreSQL database dump
--

-- Dumped from database version 12.5 (Ubuntu 12.5-0ubuntu0.20.04.1)
-- Dumped by pg_dump version 12.5 (Ubuntu 12.5-0ubuntu0.20.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: voice_activity; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.voice_activity (
    id integer NOT NULL,
    u_id bigint NOT NULL,
    online boolean DEFAULT false,
    saved_datetime timestamp without time zone NOT NULL,
    img_id character varying(255)
);


ALTER TABLE public.voice_activity OWNER TO postgres;

--
-- Name: voice_activity_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.voice_activity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.voice_activity_id_seq OWNER TO postgres;

--
-- Name: voice_activity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.voice_activity_id_seq OWNED BY public.voice_activity.id;


--
-- Name: voice_activity id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.voice_activity ALTER COLUMN id SET DEFAULT nextval('public.voice_activity_id_seq'::regclass);


--
-- Data for Name: voice_activity; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.voice_activity (id, u_id, online, saved_datetime, img_id) FROM stdin;
19	267460142889566209	f	2021-01-22 19:21:12.911273	78c53c891573e267332a51565c6bd4b3
\.


--
-- Name: voice_activity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.voice_activity_id_seq', 19, true);


--
-- PostgreSQL database dump complete
--

