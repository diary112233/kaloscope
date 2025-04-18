import { writable } from 'svelte/store';

/**
 * Type of constraints that can be applied to form inputs.
 */
export type Constraint = Partial<{
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  value: any;
  name: string;
  type: string;
  required: boolean;
  autocomplete: AutoFill;
  min: string | number;
  max: string | number;
  step: string | number;
  minlength: number;
  maxlength: number;
  pattern: string;
}>;

/**
 * Type of constraint builders.
 */
export type ConstraintBuilder =
  | StringConstraintBuilder
  | PatternConstraintBuilder
  | NumberConstraintBuilder
  | DatetimeConstraintBuilder;

/**
 * Abstract class for constraint builders.
 */
abstract class AbstractConstraintBuilder<T> {
  protected constraint: Constraint = {
    required: true
  };

  required(required: boolean): this {
    this.constraint.required = required;
    return this;
  }

  autocomplete(autocomplete: AutoFill): this {
    this.constraint.autocomplete = autocomplete;
    return this;
  }

  value(value: T): this {
    this.constraint.value = value;
    return this;
  }

  build(name: string): Constraint {
    this.constraint.name = name;
    return this.constraint;
  }
}

/**
 * Builder for string constraints.
 */
class StringConstraintBuilder extends AbstractConstraintBuilder<string> {
  minlength(minlength: number): this {
    this.constraint.minlength = minlength;
    return this;
  }

  maxlength(maxlength: number): this {
    this.constraint.maxlength = maxlength;
    return this;
  }
}

/**
 * Builder for string constraints with a RegExp pattern.
 */
class PatternConstraintBuilder extends StringConstraintBuilder {
  constructor(type: string) {
    super();
    this.constraint.type = type;
  }

  pattern(pattern: string): this {
    this.constraint.pattern = pattern;
    return this;
  }
}

/**
 * Builder for number constraints.
 */
class NumberConstraintBuilder extends AbstractConstraintBuilder<number> {
  constructor(type: string) {
    super();
    this.constraint.type = type;
  }

  min(min: number): this {
    this.constraint.min = min;
    return this;
  }

  max(max: number): this {
    this.constraint.max = max;
    return this;
  }

  step(step: number): this {
    this.constraint.step = step;
    return this;
  }
}

/**
 * Builder for datetime constraints.
 */
class DatetimeConstraintBuilder extends AbstractConstraintBuilder<string> {
  constructor(type: string) {
    super();
    this.constraint.type = type;
  }

  min(min: string): this {
    this.constraint.min = min;
    return this;
  }

  max(max: string): this {
    this.constraint.max = max;
    return this;
  }

  step(step: number | 'any'): this {
    this.constraint.step = step;
    return this;
  }
}

/**
 * Map of constraint builder factories.
 */
export const constraintBuilderFactories = {
  // textarea element
  textarea: () => new StringConstraintBuilder(),
  // input elements with type `text`, `url`, `email`, `password`
  text: () => new PatternConstraintBuilder('text'),
  url: () => new PatternConstraintBuilder('url'),
  email: () => new PatternConstraintBuilder('email'),
  password: () => new PatternConstraintBuilder('password'),
  // input elements with type `number`, `range`
  number: () => new NumberConstraintBuilder('number'),
  range: () => new NumberConstraintBuilder('range'),
  // input elements with type `datetime-local`, `date`, `time`, `week`, `month`
  datetime: () => new DatetimeConstraintBuilder('datetime-local'),
  date: () => new DatetimeConstraintBuilder('date'),
  time: () => new DatetimeConstraintBuilder('time'),
  week: () => new DatetimeConstraintBuilder('week'),
  month: () => new DatetimeConstraintBuilder('month')
};

/**
 * Create a schema of constraints for form inputs.
 *
 * @param use - A function that returns a map of constraint builders.
 * @returns A schema of constraints.
 */
export function createFormSchema<T extends Record<string, ConstraintBuilder>>(
  use: (arg: typeof constraintBuilderFactories) => T
): { [K in keyof T]: Constraint } {
  const constraintBuilders = use(constraintBuilderFactories);
  const entries = Object.entries(constraintBuilders).map(([key, builder]) => [key, builder.build(key)]);
  return Object.fromEntries(entries);
}

/**
 * Create a writable store that represents a loading state,
 * which can be set to `false`, `true`, or `null`.
 *
 * @returns A loading state store.
 */
export function createLoading() {
  const { set, update, subscribe } = writable<boolean | null>(null);

  /**
   * Set the loading state to `false` immediately and then to `true` after a delay.
   *
   * @param delay - The number of milliseconds to wait before setting the loading state to `true`.
   */
  function start(delay: number = 500) {
    set(false);
    if (delay <= 0) {
      set(true);
    } else {
      setTimeout(() => update((loading) => (loading === false ? true : loading)), delay);
    }
  }

  /**
   * Set the loading state to `null`.
   */
  function end() {
    set(null);
  }

  return { subscribe, start, end };
}

/**
 * Create a writable store that represents a sort field.
 *
 * @returns A sort field store.
 */
export function createSortField() {
  const { update, subscribe } = writable<string>('');

  /**
   * Bind a field to the sort field store.
   *
   * @param field - The field name to bind.
   * @returns An object with methods to toggle the sort order.
   */
  function bind(field: string) {
    const asc = field;
    const desc = `-${field}`;
    const toggle = () => {
      update((ordering) => {
        if (ordering === desc) {
          return asc;
        }
        if (ordering === asc) {
          return '';
        }
        return desc;
      });
    };
    return { subscribe, asc, desc, toggle };
  }

  return { subscribe, bind };
}
