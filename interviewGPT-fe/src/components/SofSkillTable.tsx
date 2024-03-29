import React, { useState } from "react";

interface SoftSkillTableProps {
  fetchSkill: {
    skills: {
      soft_skills: string[];
    };
  };
}

interface InputValues {
  [key: string]: {
    basic: number;
    intermediate: number;
    advance: number;
  };
}

const SoftSkillTable: React.FC<SoftSkillTableProps> = ({ fetchSkill }) => {
  const initialInputValues: InputValues = Object.fromEntries(
    (fetchSkill?.skills?.soft_skills || []).map((skill) => [
      skill,
      { basic: 0, intermediate: 0, advance: 0 },
    ]),
  );

  const [inputValues, setInputValues] =
    useState<InputValues>(initialInputValues);

  const handleInputChange = (
    softSkill: string,
    level: "basic" | "intermediate" | "advance",
    value: number,
  ) => {
    setInputValues((prevValues) => ({
      ...prevValues,
      [softSkill]: {
        ...(prevValues[softSkill] || { basic: 0, intermediate: 0, advance: 0 }), // Ensure the state exists
        [level]: value,
      },
    }));
  };

  const calculateTotal = (
    softSkill: string,
    level: "basic" | "intermediate" | "advance",
  ): number => {
    const skillData = inputValues[softSkill];
    return skillData ? skillData[level] : 0;
  };

  return (
    <div className="flex flex-col mx-[3rem]">
      <div className="overflow-x-auto sm:-mx-6 lg:-mx-8">
        <div className="inline-block min-w-full py-2 sm:px-6 lg:px-8">
          <div className="overflow-hidden">
            <table className="min-w-full text-left text-sm font-light border dark:border-neutral-500">
              <thead className="border-b font-medium dark:border-neutral-500">
                <tr>
                  <th scope="col" className="px-6 py-4">
                    SoftSkill
                  </th>
                  <th scope="col" className="px-6 py-4">
                    Basic Question
                  </th>
                  <th scope="col" className="px-6 py-4">
                    Intermediate
                  </th>
                  <th scope="col" className="px-6 py-4">
                    Advance
                  </th>
                  <th scope="col" className="px-6 py-4">
                    Total
                  </th>
                </tr>
              </thead>
              <tbody>
                {fetchSkill?.skills?.soft_skills.map((softSkill, index) => (
                  <tr key={index} className="border-b dark:border-neutral-500">
                    <td className="whitespace-nowrap px-6 py-4">{softSkill}</td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <input
                        className="block  mt-2 w-full placeholder-gray-400/70 dark:placeholder-gray-500 rounded-lg border border-gray-200 bg-white px-5 py-2.5 text-gray-700 focus:border-blue-400 focus:outline-none focus:ring focus:ring-blue-300 focus:ring-opacity-40 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-300 dark:focus:border-blue-300"
                        type="number"
                        value={inputValues[softSkill]?.basic || 0}
                        onChange={(e) =>
                          handleInputChange(
                            softSkill,
                            "basic",
                            parseInt(e.target.value, 10) || 0,
                          )
                        }
                      />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <input
                        className="block  mt-2 w-full placeholder-gray-400/70 dark:placeholder-gray-500 rounded-lg border border-gray-200 bg-white px-5 py-2.5 text-gray-700 focus:border-blue-400 focus:outline-none focus:ring focus:ring-blue-300 focus:ring-opacity-40 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-300 dark:focus:border-blue-300"
                        type="number"
                        value={inputValues[softSkill]?.intermediate || 0}
                        onChange={(e) =>
                          handleInputChange(
                            softSkill,
                            "intermediate",
                            parseInt(e.target.value, 10) || 0,
                          )
                        }
                      />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <input
                        className="block  mt-2 w-full placeholder-gray-400/70 dark:placeholder-gray-500 rounded-lg border border-gray-200 bg-white px-5 py-2.5 text-gray-700 focus:border-blue-400 focus:outline-none focus:ring focus:ring-blue-300 focus:ring-opacity-40 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-300 dark:focus:border-blue-300"
                        type="number"
                        value={inputValues[softSkill]?.advance || 0}
                        onChange={(e) =>
                          handleInputChange(
                            softSkill,
                            "advance",
                            parseInt(e.target.value, 10) || 0,
                          )
                        }
                      />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <span>
                        {calculateTotal(softSkill, "basic") +
                          calculateTotal(softSkill, "intermediate") +
                          calculateTotal(softSkill, "advance")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SoftSkillTable;
