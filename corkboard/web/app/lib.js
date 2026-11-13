// Preact and htm, imported once so every module shares the same copy.
import { Fragment, createContext, h, render } from "../vendor/preact.module.js";
import {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "../vendor/hooks.module.js";
import htm from "../vendor/htm.module.js";

export const html = htm.bind(h);
export {
  Fragment,
  createContext,
  render,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
};
